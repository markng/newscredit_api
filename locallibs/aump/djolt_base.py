#
#	djolt_base.py
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

import bm_extract

from bm_log import Log

try:
	import json
except ImportError:
	import simplejson as json

class DjoltError(Exception): pass
class DjoltSyntaxError(DjoltError): pass
class DjoltNoSuchFilterError(DjoltError): pass
class DjoltNoSuchTagError(DjoltError): pass
class DjoltUnknownArgumentError(DjoltError): pass

noded = {}

#
#
#
class Node:
	_name = None
	nonhierarchical = False

	def __init__(self, parent = None):
		self.parent = parent
		self.children = []

		if self.parent:
			self.parent.AddChild(self)

	def AddChild(self, child):
		self.children.append(child)

	def Render(self, results, context):
		for child in self.children:
			child.Render(results, context)

	def PopExpecting(self, parents = None):
		if parents:
			found = False
			for parent in bm_extract.coerce_list(parents):
				if parent == self.__class__:
					found = True

			if not found:
				raise	DjoltSyntaxError, "expected one of: %s got: %s" % ( ", ".join(map(lambda c: c.__name__, parents)), self.__class__, )

		return	self.parent

	def Dump(self, depth = 0):
		print " " * depth * 2 + self.__class__.__name__
		for child in self.children:
			child.Dump(depth + 1)

	def Start(self, template_src, startx):
		pass

	def End(self, template_src, endx):
		pass

	def Register(cls):
		noded[cls._name] = cls

	Register = classmethod(Register)

	def Find(cls, name):
		return	noded.get(name)

	Find = classmethod(Find)

filterd = {}

#
#
#
class Filter:
	_name = None

	def __init__(self):
		global filterd

		if not self._name:
			Log("filter missing name", filter = self.__class__.__name__)
			return

		filterd[self._name] = self

	def Find(cls, name):
		return	filterd.get(name)

	Find = classmethod(Find)

	def Filter(self, name, argument, value):
		raise	NotImplementedError

#
#	This is tied to djolt_loader, djolt_components
#
a_re = r"""
	(?P<var>[a-z][a-z0-9._]*)
	(
		:"(?P<a1>[^"]*)"
		|
		:'(?P<a2>[^']*)'
		|
		:(?P<a3>[^\s]+)
	)?
"""
a_rex = re.compile(a_re, re.I|re.DOTALL|re.MULTILINE|re.VERBOSE|re.UNICODE)

standard_argumentd = {
	"meta" : "in_meta_path",
	"items" : "in_items_path",
	"meta_map" : "in_meta_map_path",
	"items_map" : "in_items_map_path",
	"render" : "render",

	"from" : "from_path",
	"as" : "to_path",
	"to" : "to_path",
	"using" : "using_path",
}

class ComponentArguments:
	component_name = None

	in_meta_path = None
	in_meta_map_path = None
	in_items_path = None
	in_items_map_path = None
	render = True

	as_path = None

	from_path = None
	to_path = None
	using_path = None

	def __init__(self, widget_name, arguments):
		"""
		Arguments look like this

		{% widget <widget-name> a:"value" b:value c:'value' d %}

		This returns ( <widget-name>, { "a" : "value", "b" : "value", "c" : "value", d : None } )
		"""

		parts = arguments.split(" ", 1)
		if not parts:
			raise	djolt_base.DjoltSyntaxError, "too few arguments for '%s'" % widget_name

		self.component_name = parts[0]

		if len(parts) == 2:
			for m in a_rex.finditer(parts[1]):
				key = m.group('var')
				value = m.group('a1') or m.group('a2') or m.group('a3') or None

				if key == "render":
					value = bm_extract.coerce_bool(value, otherwise = True)

				key_var = standard_argumentd.get(key)
				if not key_var:
					raise	DjoltUnknownArgumentError, key

				setattr(self, key_var, value)

#
#
#
class Mapper:
	"""Define a way of moving from one WORK object to another using 'mappingd'"""

	def __init__(self, mappingd, context):
		self.mappingd = mappingd
		self.context = context

	def Map(self, items):
		for itemd in items:
			yield	self.MapItem(itemd)

	def MapItem(self, itemd):
		return	self.Clone(self.mappingd)

