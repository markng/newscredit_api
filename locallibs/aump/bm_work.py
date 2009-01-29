#
#   bm_work.py
#
#   David Janes
#   2008.11.01
#
#	Copyright 2008 David Janes
#

import os
import sys
import urllib
import types
import pprint
import types
import re

try:
	import json
except:
	import simplejson as json

import bm_extract
import bm_uri
import bm_text

from bm_log import Log

import xml.etree.ElementTree as ElementTree

## #
## #	Phase Me Out ... this is a bad idea
## #
## class WORK(dict):
## 	def __init__(self, *av, **ad):
## 		dict.__init__(self, *av, **ad)
## 		self._entered = False
## 
## 	def __getitem__(self, path):
## 		if self._entered:
## 			return	dict.__getitem__(self, path)
## 
## 		try:
## 			self._entered = True
## 
## 			o = bm_extract.extract(self, path)
## 
## 			return	o
## 		finally:
## 			self._entered = False
## 
## 	def get(self, path, othewise = None):
## 		if self._entered:
## 			return	dict.get(self, path, otherwise)
## 
## 		try:
## 			self._entered = True
## 
## 			o = bm_extract.extract(self, path)
## 
## 			return	o
## 		finally:
## 			self._entered = False
## 
## 	def as_float(self, path, **ad):
## 		return	bm_extract.as_float(self, path, **ad)
## 
## 	def as_int(self, path, **ad):
## 		return	bm_extract.as_int(self, path, **ad)
## 
## 	def as_bool(self, path, **ad):
## 		return	bm_extract.as_bool(self, path, **ad)
## 
## 	def as_list(self, path, **ad):
## 		return	bm_extract.as_list(self, path, **ad)
## 
## 	def as_string(self, path, **ad):
## 		return	bm_extract.as_string(self, path, **ad)

sluggie_rex = re.compile(u"[^a-z0-9_:]", re.I|re.DOTALL)
underscore_rex = re.compile("_+")

class Sluggifier:
	"""This ensures that keys conform to WORK rules"""

	def __init__(self, sluggifier = None, strip_empty_strings = True):
		self.SluggifyString = sluggifier or self._standard_sluggifier
		self.strip_empty_strings = strip_empty_strings

	def SluggifyObject(self, o):
		if type(o) == types.DictType:
			for key, value in list(o.iteritems()):
				self.SluggifyObject(value)

				if self.strip_empty_strings and value == "":
					try: del o[key]
					except: pass

					continue

				nkey = self.SluggifyString(key)
				if nkey != key:
					o[nkey] = value

					try: del o[key]
					except: pass
		elif type(o) == types.ListType:
			for value in o:
				self.SluggifyObject(value)

	def _standard_sluggifier(self, value):
		value = sluggie_rex.sub("_", value)
		value = underscore_rex.sub("_", value)
		value = value.strip("_")

		return	value

class XML2WORK:
	"""Convert an XML document to a WORK object
	
	WORK is documented here:
	http://code.davidjanes.com/blog/2008/11/11/work-web-object-records/

	If your API doesn't return anything, it's likely the data as stored 
	as attributes and you should set 'keep_attributes' to True
	"""

	def __init__(self, keep_attributes = False, attribute_prefix = '@'):
		self.keep_attributes = keep_attributes
		self.attribute_prefix = attribute_prefix

	def FeedFile(self, file):
		try:
			fin = open(file, 'rb')
			return	self.FeedString(fin.read())
		finally:
			try: fin.close()
			except: pass

	def FeedString(self, data):
		if not data:
			return	{}

		data = bm_text.toutf8(data)
		et = ElementTree.fromstring(data)

		return	self._NodeConverter(et)

	def FeedURI(self, uri):
		pass

	def CustomizeTagIgnore(self, tpath):
		return	False

	def CustomizeTagIsPath(self, tpath):
		return	None

	def _TagScrubber(self, tag):
		bracketx = tag.rfind('}')
		if bracketx > -1:
			tag = tag[bracketx + 1:]

		return	tag

	def _NodeConverter(self, node0, path = None, itemd = None):
		if itemd == None:
			itemd = {}

		if path == None:
			path = []

		for node1 in node0:
			tag1 = self._TagScrubber(node1.tag)
			value1 = (node1.text or "").strip()

			npath = list(path)
			npath.append(tag1)
			npathdot = ".".join(npath)

			if self.CustomizeTagIgnore(npathdot):
				continue

			if not value1:
				value1 = self._NodeConverter(node1, npath)
			
			if not value1 and not self.keep_attributes:
				continue

			is_path = self.CustomizeTagIsPath(npathdot)
			if is_path == None:
				if itemd.get(tag1):
					if type(itemd.get(tag1)) == types.ListType:
						itemd[tag1].append(value1)
					else:
						itemd[tag1] = [ itemd[tag1], value1 ]
				else: 
					itemd[tag1] = value1
			elif is_path == False:
				itemd[tag1] = value1
			else:
				itemd.setdefault(tag1, []).append(value1)

		#
		#
		#
		if self.keep_attributes and node0.attrib:
			for key, value in node0.attrib.iteritems():
				itemd['%s%s' % ( self.attribute_prefix, key, )] = value

		return	itemd

class HTML2WORK:
	"""Convert an HTML document encoded in XML to a WORK object
	
	WORK is documented here:
	http://code.davidjanes.com/blog/2008/11/11/work-web-object-records/
	"""

	def __init__(self, keep_attributes = True, attribute_prefix = '@'):
		self.keep_attributes = keep_attributes
		self.attribute_prefix = attribute_prefix

	def FeedFile(self, file):
		try:
			fin = open(file, 'rb')
			return	self.FeedString(fin.read())
		finally:
			try: fin.close()
			except: pass

	def FeedString(self, data):
		if not data:
			return	{}

		data = bm_text.toutf8(data)
		et = ElementTree.fromstring(data)

		d = self._NodeConverter(et)
		d = self._ResultScrubber(d)

		return	d

	def FeedURI(self, uri):
		pass

	def CustomizeTagIgnore(self, tpath):
		return	False

	def CustomizeTagIsPath(self, tpath):
		return	None

	def _TagScrubber(self, tag):
		bracketx = tag.rfind('}')
		if bracketx > -1:
			tag = tag[bracketx + 1:]

		return	tag

	def _ResultScrubber(self, d, depth = 0):
		if type(d) == types.ListType:
			ds = []

			for subd in d:
				result = self._ResultScrubber(subd, depth = depth + 1)
				if result:
					ds.append(result)

			return	ds
		elif type(d) == types.DictType:
			for key, subd in list(d.iteritems()):
				newd = self._ResultScrubber(subd, depth = depth + 1)
				if not newd:
					del d[key]
				else:
					d[key] = newd

			if len(d) == 1 and d.has_key('@'):
				return	d['@'] or None

			return	d
		else:
			return	d or None

	def _NodeConverter(self, node0, first = True):
		#
		#	This node's core data
		#
		tag0 = self._TagScrubber(node0.tag)
		text0 = (node0.text or "")
		tail0 = (node0.tail or "")

		#
		#	All the children of this node
		#
		children = []

		for node1 in node0:
			result1 = self._NodeConverter(node1, first = False)
			if result1:
				children.append(result1)

		#
		#	This node ... the '@tag' will be popped by the parent
		#
		itemd = {
			"@tag" : tag0,
		}

		texts = []
		texts.append(text0)

		#
		#	Children ... 
		#
		for child in children:
			tag1 = child.pop("@tag")

			if not itemd.has_key(tag1):
				itemd[tag1] = child
			elif type(itemd.get(tag1)) == types.ListType:
				itemd[tag1].append(child)
			else:
				itemd[tag1] = [ itemd[tag1], child ]

			add_space = tag1 in [ 
				'p', 'div', 'br', 'hr',
				'h1', 'h2', 'h3', 'h4', 'h5', 'h6',     
				'table', 'tr', 'td', 'thead', 'tbody', 'tfoot',
			]

			text = child.pop("@text")
			if add_space:
				texts.append('\n')
				texts.append(text)
				texts.append('\n')
			else:
				texts.append(text)

		#
		#	Make the text
		#
		texts.append(tail0)
		text = ''.join(texts)
		itemd['@text'] = text
		text = ' '.join(text.split())
		itemd['@'] = text

		#
		#	At the top (essentially HTML) level we 
		#	don't keep '@' up to this point
		#
		if first:
			for key in list(itemd.keys()):
				if key.startswith('@'):
					try: del itemd[key]
					except: pass

		#
		#	HTML attributes
		#
		if self.keep_attributes and node0.attrib:
			for key, value in node0.attrib.iteritems():
				itemd['%s%s' % ( self.attribute_prefix, key, )] = value

		return	itemd

jsonp_re = """^\s*[^(\s]+[(](?P<json>.*)[)];*\s*$"""
jsonp_rex = re.compile(jsonp_re, re.MULTILINE|re.DOTALL)

class JSON2WORK(Sluggifier):
	"""Convert an JSON document to a WORK object
	
	WORK is documented here:
	http://code.davidjanes.com/blog/2008/11/11/work-web-object-records/
	"""

	def __init__(self, sluggifier = None, strip_empty_strings = True):
		Sluggifier.__init__(self, sluggifier = sluggifier, strip_empty_strings = strip_empty_strings)

	def FeedFile(self, file):
		try:
			fin = open(file, 'rb')
			return	self.FeedString(fin.read())
		finally:
			try: fin.close()
			except: pass

	def FeedString(self, data):
		if data[:1] not in [ '{', '[', ]:
			jsonp_match = jsonp_rex.match(data)
			if jsonp_match:
				data = jsonp_match.group('json')

		o = json.loads(data)
		self.SluggifyObject(o)

		return	o

	def FeedURI(self, uri):
		pass

#
#	Make sure we can deal with weird objects
#
class IterEncoder(json.JSONEncoder):
	""" """
	def default(self, o):
		try:
			return	json.JSONEncoder.default(self, o)
		except TypeError, x:
			try:
				return	list(iter(o))
			except:
				return	x

#
#	Remove dictionary keys with '@@'
#
class ScrubIterEncoder(IterEncoder):
	""" """
	def _iterencode(self, o, *av, **ad):
		if bm_extract.is_dict(o):
			no = {}

			for key, value in o.iteritems():
				if key.find('@@') == -1:
					no[key] = value

			o = no

		return	json.JSONEncoder._iterencode(self, o, *av, **ad)

if __name__ == '__main__':
	sample = """
<html>
	<a href="bla">
		Assertion:
		<em class="sport">
			Basketball
		</em>
		and
		<em>
			Blurnball
		</em>
		are
		<strong class="class" style="">
			Sports
		</strong>
		(of sorts)
	</a>
</html>
"""
	converter = HTML2WORK(keep_attributes = True)
	pprint.pprint(converter.FeedString(sample), width = 1)
