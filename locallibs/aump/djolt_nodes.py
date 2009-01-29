#
#	djolt_nodes.py
#	- djolt - Django-like templates
#
#	David Janes
#	2008.11.18
#
#	Copyright 2008 David Janes
#
#	Nodes define {% ... %} and {{ ... }} items in the template
#
#	The main class you want to look at is 'Template', everything
#	else is just support. 
#

import sys
import os
import re
import random
import types

try:
	import json
except ImportError:
	import simplejson as json

import bm_extract

import djolt_base
import djolt_filters

from bm_log import Log

SPECIAL_SAFE = "@_SAFE"

filters_re = r"""
	[|]
	(?P<filter>[a-z][_a-z0-9]+)
	(
		:"(?P<a1>[^"]*)"
		|
		:'(?P<a2>[^']*)'
		|
		:(?P<a3>[^ |]+)
	)?
"""
filters_rex = re.compile(filters_re, re.I|re.DOTALL|re.MULTILINE|re.VERBOSE|re.UNICODE)

class NodeRoot(djolt_base.Node):
	pass

class NodeVariable(djolt_base.Node):
	def __init__(self, path, filters, indirection = 0):
		djolt_base.Node.__init__(self)

		self.path = path
		self.filters = []
		self.indirection = indirection

		self._parse_filters(filters)

	def Render(self, results, context):
		import djolt

		value = context.get(self.path)
		indirection  = self.indirection
		while indirection > 0:
			try:
				indirection -= 1

				if not value:
					break

				value = bm_extract.coerce_string(value, separator = None)

				context.Push()
				try:
					context[SPECIAL_SAFE] = True
					value = djolt.Template(value).Render(context)
				finally:
					context.Pop()
			except:
				results.append("<pre>\n" + Log(
					"Indirect template exception",
					exception = True,
					indirection = self.indirection,
					path = self.path,
				).replace("\n", "<br />") + "\n</pre>")
				return

		is_safe = context.get(SPECIAL_SAFE, True)

		for filter_name, filter_argument in self.filters:
			if filter_name == "safe":
				is_safe = False
				continue
			elif filter_name == "escape":
				is_safe = True
				continue
				
			filter = djolt_base.Filter.Find(filter_name)
			if not filter:
				raise	djolt_base.DjoltNoSuchFilterError, filter_name

			value = filter.Filter(filter_name, filter_argument, value)

		if is_safe and type(value) in types.StringTypes:
			value = value.replace("&", "&amp;");
			value = value.replace("<", "&lt;");
			value = value.replace(">", "&gt;");
			value = value.replace("'", "&#39;");
			value = value.replace("\"", "&quot;");

		results.append(value)

	def _parse_filters(self, filters):
		for filter_match in filters_rex.finditer(filters or ""):
			filter_name = filter_match.group('filter')
			filter_argument = filter_match.group('a1') or filter_match.group('a2') or filter_match.group('a3')

			self.filters.append(( filter_name, filter_argument ))

class NodeText(djolt_base.Node):
	def __init__(self, text):
		djolt_base.Node.__init__(self)
		self.text = text

	def Render(self, results, context):
		results.append(self.text)

expr_rex = re.compile("""
	(
		(?P<f2>
			int|bool|float|string
		)
		[(]
		\s*
		(?P<x2>
			[a-z]\w*
			(
				(
					[[]\d+[]]
				)
				|
				(
					[.][a-z]\w*
				)
			)*
		)
		\s*
		[)]
	)
	|
	(?P<x1>
		[a-z]\w*
		(
			(
				[[]\d+[]]
			)
			|
			(
				[.][a-z]\w*
			)
		)*
	)
""", re.VERBOSE|re.I)

##		if function == "bool":
##			return	bm_extract.coerce_bool(raw_value) and "1" or "0"
##		elif function == "int":
##			return	"%s" % bm_extract.coerce_int(raw_value)
##		elif function == "float":
##			return	"%s" % bm_extract.coerce_float(raw_value)
##		elif function == "string":
##			return	repr(bm_extract.coerce_string(raw_value))
##		else:
##			raise	NotImplementedError

class NodeIf(djolt_base.Node):
	_name = "if"

	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

		self.arguments = arguments

	def Test(self, context):
		import djolt_expression

		return	bm_extract.coerce_bool(djolt_expression.parse(self.arguments).Execute(context))

	def Render(self, results, context):
		if self.Test(context):
			djolt_base.Node.Render(self, results, context)

NodeIf.Register()

class NodeIfElse(NodeIf):
	_name = "else-if"

	def __init__(self, parent, if_node):
		NodeIf.__init__(self, parent, if_node.arguments)

	def Render(self, results, context):
		if not self.Test(context):
			djolt_base.Node.Render(self, results, context)

NodeIfElse.Register()

RE_MATCH = "match"
RE_SEARCH = "search"
RE_ITER = "iter"

class NodeRegex(djolt_base.Node):
	_name = "regex"

	def __init__(self, parent, arguments, mode):
		djolt_base.Node.__init__(self, parent)

		self.arguments = arguments
		self.parts = self.arguments.split(' ', 1)
		self.mode = mode

		if len(self.parts) != 2:
			raise	djolt_base.DjoltSyntaxError, "wrong arguments to '%s': %s" % ( self._name, self.arguments, )

		self.variable = self.parts[0]
		self.re = self.parts[1]
		self.rex = re.compile(self.re)

	def Matches(self, context):
		value = context.as_string(self.variable)

		if self.mode == RE_SEARCH:
			match = self.rex.search(value)
			if match:
				return	[ match ]
		elif self.mode == RE_MATCH:
			match = self.rex.match(value)
			if match:
				return	[ match ]
		elif self.mode == RE_ITER:
			return	list(self.rex.finditer(value))
		else:
			assert(False)

		return	[]

	def Render(self, results, context):
		for match in self.Matches(context):
			context.Push()

			context['0'] = match.group(0)
			
			count = 0
			for v in match.groups():
				count += 1
				context['%d' % count] = v

			djolt_base.Node.Render(self, results, context)

			context.Pop()

NodeRegex.Register()

class NodeRegexElse(NodeRegex):
	_name = "else-regex"

	def __init__(self, parent, regex_node):
		NodeRegex.__init__(self, parent, regex_node.arguments, regex_node.mode)

	def Render(self, results, context):
		if not self.Matches(context):
			djolt_base.Node.Render(self, results, context)

NodeRegexElse.Register()

class NodeEqual(djolt_base.Node):
	_name = "equal"

	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

NodeEqual.Register()

class NodeFor(djolt_base.Node):
	"""
	Syntax:
		for <variable> in <path>

	Restrictions:
		<path> must be in the context, you cannot directly embed a python list (yet)
	"""
	_name = "for"

	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

		parts = arguments.split()
		if len(parts) != 3:
			raise	djolt_base.DjoltSyntaxError, "wrong arguments to 'for': %s" % parts

		self.variable = parts[0]
		self.path = parts[2]

	def Render(self, results, context):
		value = context.get(self.path)
		if value == None:
			return

		values = bm_extract.coerce_list(value, separator = ", ")
		if not values:
			return

		count = -1
		for v in values:
			count += 1

			context.Push()
			context[self.variable] = v
			context["forloop.counter"] = count + 1						# iteration of the loop (1-indexed)
			context["forloop.counter0"] = count							# iteration of the loop (0-indexed)
			context["forloop.revcounter"] = len(values) - count			# iterations from the end of the loop (1-indexed)
			context["forloop.revcounter0"] = len(values) - count - 1	# iterations from the end of the loop (0-indexed)
			context["forloop.first"] = bool(count == 0) 				# True if this is the first time through the loop
			context["forloop.last"] = bool(count == len(values) - 1)	# True if this is the last time through the loop

			djolt_base.Node.Render(self, results, context)

			context.Pop()

NodeFor.Register()

class NodeRegroup(djolt_base.Node):
	"""Regroup a list of alike objects by a common attribute.
	
	<pre>
{% regroup people by gender as gender_list %}

<ul>
{% for gender in gender_list %}
    <li>{{ gender.grouper }}
    <ul>
        {% for item in gender.list %}
        <li>{{ item.first_name }} {{ item.last_name }}</li>
        {% endfor %}
    </ul>
    </li>
{% endfor %}
</ul>
	</pre>

	XXX - NEED TO BE ABLE TO TAKE ARGUMENTS TO VARIABLE
	"""

	_name = "regroup"
	nonhierarchical = True

	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

		self.arguments = arguments

		parts = arguments.split()
		if len(parts) != 5 or parts[1] != "by" or parts[3] != "as":
			raise	djolt_base.DjoltSyntaxError, "wrong arguments to 'regroup': %s" % arguments

		self.input = parts[0]
		self.grouper = parts[2]
		self.output = parts[4]

	def Render(self, results, context):
		results = []
		currentd = {}

		last_grouper = bm_extract.MARKER

		items = context.as_list(self.input)
		for itemd in items:
			grouper = bm_extract.extract(itemd, self.grouper)
			if grouper == None:
				continue

			if grouper != last_grouper:
				last_grouper = grouper

				currentd = {
					"grouper" : grouper,
					"list" : [],
				}
				results.append(currentd)

			currentd["list"].append(itemd)

		context[self.output] = results
			

NodeRegroup.Register()

class NodeAutoEscape(djolt_base.Node):
	_name = "autoescape"

	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

		self.arguments = arguments

	def Render(self, results, context):
		context.Push()

		if self.arguments == "off":
			context[SPECIAL_SAFE] = False
		elif self.arguments == "on":
			context[SPECIAL_SAFE] = True
		else:
			raise	djolt_base.DjoltSyntaxError, "bad argument for 'autoescape': %s" % self.arguments

		result = djolt_base.Node.Render(self, results, context)

		context.Pop()

		return	result

NodeAutoEscape.Register()

class NodeExact(djolt_base.Node):
	"""Abstract base class for nodes that take their contents exactlt
	"""
	def __init__(self, parent, arguments):
		djolt_base.Node.__init__(self, parent)

		self.arguments = arguments

	def Start(self, template_src, startx):
		self.startx = startx
		self.text = None

	def End(self, template_src, endx):
		self.text = template_src[self.startx:endx]

	def Render(self, results, context):
		raise	NotImplementError

class NodeAsis(NodeExact):
	_name = "asis"

	def Render(self, results, context):
		results.append(self.text)

NodeAsis.Register()
