#
#	djolt.py
#	- djolt - Django-like templates
#
#	David Janes
#	2008-11-18
#
#	Copyright 2008 David Janes
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
import djolt_nodes

from bm_log import Log

djolt_re = r"""
	(
		(
			^\s+
		)?
		{%
		\s*
		(?P<block>
			(?P<tag>[a-z]+)
			(
				\s+
				(?P<bargs>.*?)
			)?
		\s*
		)
		%}
		(
			[ \t]*$\n
		)?
	|
		{{
		\s*
		(?P<variable>
			(?P<indirection>[*]*)
			(?P<path>[-@_a-zA-Z.\[\]0-9'":]+)	# wrong!
			(?P<filters>
				\s*[|]\s*
				.*?
			)?
		)
		\s*
		}}
	)
"""
djolt_rex = re.compile(djolt_re, re.I|re.DOTALL|re.MULTILINE|re.VERBOSE|re.UNICODE)

class Context:
	def __init__(self, *dv):
		self.stack = [ {} ]
		for d in dv:
			self.Push(d)

	def get(self, key, otherwise = None):
		"""Make this a little dict-like looking"""

		for d in self.stack:
			value = bm_extract.extract(d, key, otherwise = otherwise)
			if value != None:
				return	value

		return	None

	def as_float(self, path, **ad):
		return	bm_extract.coerce_float(self.get(path), **ad)

	def as_int(self, path, **ad):
		return	bm_extract.coerce_int(self.get(path), **ad)

	def as_bool(self, path, **ad):
		return	bm_extract.coerce_bool(self.get(path), **ad)

	def as_list(self, path, **ad):
		return	bm_extract.coerce_list(self.get(path), **ad)

	def as_dict(self, path, **ad):
		return	bm_extract.coerce_dict(self.get(path), **ad)

	def as_string(self, path, **ad):
		return	bm_extract.coerce_string(self.get(path), **ad)

	def as_datetime(self, path, **ad):
		return	bm_extract.coerce_datetime(self.get(path), **ad)

	def __setitem__(self, key, value):
		"""Make this a little dict-like looking"""

		bm_extract.set(self.stack[0], key, value)

	def Top(self):
		return	self.stack[0]

	def Bottom(self):
		return	self.stack[-1]

	def Push(self, d = None):
		self.stack.insert(0, d or {})

	def Pop(self):
		self.stack.pop(0)

class Template:
	"""Create and manipilate a Djolt template"""

	def __init__(self, template):
		self._parse(template)

	def render(self, *av, **ad):
		"""For compatibility with Django's style"""

		return	self.Render(*av, **ad)
		
	def Render(self, context = {}):
		if not isinstance(context, Context):
			assert(isinstance(context, dict)), "context must be a Context object or dict"
			context = Context(context)

		results = []
		self.node.Render(results, context)

		results = filter(lambda r: r != None, results)

		#
		#	See Filter_raw
		#	- we need this complicated logic due to empty spaces
		#	sometimes being inserted into the template
		#
		if len(results) > 0:
			for result in results:
				if isinstance(result, bm_extract.AsIs):
					return	result.value
				elif result != '':
					break

		results = map(lambda x: bm_extract.coerce_string(x, separator = ", "), results)

		return	"".join(results)

	def _parse(self, template_src):
		self.node = None
		self._feed_sof()
		current = 0

		for djolt_match in djolt_rex.finditer(template_src):
			self._feed_text(template_src[current:djolt_match.start()])
			current = djolt_match.end()

			if djolt_match.group('block'):
				self._feed_block(
					djolt_match.group('tag'), 
					djolt_match.group('bargs'), 
					djolt_match,
					template_src,
				)
			elif djolt_match.group('variable'):
				self._feed_variable(
					djolt_match.group('path'), 
					djolt_match.group('filters'), 
					djolt_match,
					template_src,
					indirection = len(djolt_match.group('indirection') or ""),
				)

		self._feed_text(template_src[current:])
		self._feed_eof()

	def _feed_sof(self):
		self.node = djolt_nodes.NodeRoot()

	def _feed_eof(self):
		if self.node.__class__ != djolt_nodes.NodeRoot:
			raise	Exception, "wrong node (expected to see end of file)"

	def _feed_text(self, text):
		self.node.AddChild(djolt_nodes.NodeText(text))
			
	def _feed_variable(self, path, filters, match, template_src, indirection = 0):
		self.node.AddChild(djolt_nodes.NodeVariable(path, filters, indirection = indirection))
			
	def _feed_block(self, tag, arguments, match, template_src):
		method = "_feed_block_%s" % tag
		if hasattr(self, method):
			return	getattr(self, method)(tag, arguments, match, template_src)

		is_start = True
		if tag.startswith("end"):
			tag = tag[3:]
			is_start = False

		node_class = djolt_base.Node.Find(tag)
		if not node_class:
			raise	djolt_base.DjoltNoSuchTagError, tag

		if is_start:
			self.node = node_class(self.node, arguments)
			self.node.Start(template_src, match.end())

			if self.node.nonhierarchical:
				self.node.End(template_src, match.start())
				self.node = self.node.PopExpecting(node_class)
		else:
			self.node.End(template_src, match.start())
			self.node = self.node.PopExpecting(node_class)

	def _feed_block_if(self, tag, arguments, match, template_src):
		self.node = djolt_nodes.NodeIf(self.node, arguments)
		self.node.Start(template_src, match.end())

	def _feed_block_research(self, tag, arguments, match, template_src):
		self.node = djolt_nodes.NodeRegex(self.node, arguments, mode = djolt_nodes.RE_SEARCH)
		self.node.Start(template_src, match.end())

	def _feed_block_rematch(self, tag, arguments, match, template_src):
		self.node = djolt_nodes.NodeRegex(self.node, arguments, mode = djolt_nodes.RE_MATCH)
		self.node.Start(template_src, match.end())

	def _feed_block_reiter(self, tag, arguments, match, template_src):
		self.node = djolt_nodes.NodeRegex(self.node, arguments, mode = djolt_nodes.RE_ITER)
		self.node.Start(template_src, match.end())

	def _feed_block_else(self, tag, arguments, match, template_src):
		start_node = self.node
		parent_node = self.node.PopExpecting([ djolt_nodes.NodeIf, djolt_nodes.NodeRegex ])

		if isinstance(start_node, djolt_nodes.NodeIf):
			self.node = djolt_nodes.NodeIfElse(parent_node, start_node)
			self.node.Start(template_src, match.end())
		elif isinstance(start_node, djolt_nodes.NodeRegex):
			self.node = djolt_nodes.NodeRegexElse(parent_node, start_node)
			self.node.Start(template_src, match.end())
		else:
			Log(parent_node = parent_node, start_node = start_node)
			assert(False)

	def _feed_block_endif(self, tag, arguments, match, template_src):
		self.node.End(template_src, match.start())
		self.node = self.node.PopExpecting([ djolt_nodes.NodeIf, djolt_nodes.NodeIfElse, ])

	def _feed_block_endresearch(self, tag, arguments, match, template_src):
		self.node.End(template_src, match.start())
		self.node = self.node.PopExpecting([ djolt_nodes.NodeRegex, djolt_nodes.NodeRegexElse, ])

	def _feed_block_endrematch(self, tag, arguments, match, template_src):
		self.node.End(template_src, match.start())
		self.node = self.node.PopExpecting([ djolt_nodes.NodeRegex, djolt_nodes.NodeRegexElse, ])

	def _feed_block_endreiter(self, tag, arguments, match, template_src):
		self.node.End(template_src, match.start())
		self.node = self.node.PopExpecting([ djolt_nodes.NodeRegex, djolt_nodes.NodeRegexElse, ])

#
#
#
def RenderObject(o, context):
	"""Return a clone of 'o', except that all strings are treated as templates"""

	if isinstance(o, dict):
		d = {}
		for key, value in o.iteritems():
			d[key] = RenderObject(value, context)

		return	d
	elif isinstance(o, list):
		l = []
		for value in o:
			l.append(RenderObject(value, context))

		return	l
	elif type(o) in types.StringTypes:
		if context != None:
			template = Template(o)
			return	template.render(context)
		else:
			return	o
	else:
		return	o

