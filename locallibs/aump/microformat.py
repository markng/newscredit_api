#
#	microformat.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
#

import sys

import os
import pprint
import types
import re
import copy
import urlparse
import urllib

import xml.dom.minidom
import xml.dom
import xml.sax
import xml.sax.handler

from bm_log import Log
import bm_uri
import bm_text

import uf_mfdict

NO_TITLE = '[Missing Title]'

#
#	The types of data that can be retrieved from the DOM
#
TT_STRING = 10				# no newlines
TT_TEXT = 20				# text, with newlines
TT_ABBR = 30				# the contents of the ABBR, otherwise the MF_TEXT
TT_ABBR_DT = 31				# the contents of the ABBR, otherwise the MF_TEXT; Datetimes only!
TT_XML = 40					#
TT_XML_OUTER = 40			# XML text, including the element
TT_XML_INNER = 41			# XML text, excluding the element (i.e. all the children)
TT_INT = 50					# integer value
TT_FLOAT = 51				# floating point value

#
#
#
class MicroformatError(Exception):
	def __init__(self, msg = None):
		Exception.__init__(self, msg)

class MicroformatInvalid(MicroformatError):
	def __init__(self, msg = None):
		Exception.__init__(self, msg)

class Microformat:
	def __init__(self,
	  root_name,
	  uf_name,
	  root_type = "class",
	  collect_ids = False,
	  page_uri = None,
	  include = False,
	  scrub_scripts = True,
	  keep_html = None,		# see code
	  parent = None,
	  ):
		self.root_name = root_name
		self.uf_name = uf_name
		self.root_type = root_type	# class, rel
		self.collect_ids = collect_ids or include
		self.root_element = None
		self.page_uri = page_uri
		self.actions = {}
		self.repeats = []
		self.uris = []
		self.repeat_count = {}
		self.intermediates = []
		self.id_map = {}
		self.data = uf_mfdict.mfdict()
		self.dom = None
		self.is_include = include
		self.is_scrub_scripts = scrub_scripts
		self.is_keep_html = bool(keep_html)

		self.title_class = None
		self.bookmark_class = None

		self.index_count = 0

		self.parent = parent
		if self.parent:
			self.is_scrub_scripts = parent.is_scrub_scripts
			self.is_include = False				# is already done!
			self.page_uri = parent.page_uri
			
			if keep_html == None:
				self.is_keep_html = False
		else:
			if keep_html == None:
				self.is_keep_html = True

		self.Reset()

	def Iterate(self):
		if not self.dom:
			self.PragmaCLI()

		if not self.dom:
			raise	MicroformatError("Programming error - no document specified")

		self.id_to_element = {}
		self.index_count = 0

		if self.collect_ids:
			for root_element in self.dom.getElementsByTagName("*"):
				id = root_element.getAttribute("id")
				if id:
					self.id_map[id] = root_element

		for root_element in self.dom.getElementsByTagName("*"):
			value = root_element.getAttribute(self.root_type)
			if not value or not self.root_name in value.split():
				continue

			self.index_count += 1

			if self.is_keep_html:
				html = root_element.toxml('utf8').decode('utf8')
				if self.is_scrub_scripts:
					html = bm_text.scrub_html(html, bm_text.SCRUB_SCRIPTS|bm_text.SCRUB_CLEANUP)
			else:
				html = ''

			if self.is_include:
				root_element = self.DoIncludePattern(root_element)

			try:
				self.Start(root_element)

				for child_element in root_element.getElementsByTagName("*"):
					self.Add(child_element)

				self.End()

				self.data['@index'] = "%s-%d" % ( self.root_name, self.index_count )
				self.data['@uf'] = self.uf_name
				self.data.setdefault('@html', html)
				self.data.setdefault('@title', NO_TITLE)

				tag_name = root_element.tagName
				root_element.tagName = "div"
				root_element.tagName = tag_name

				if self.data.get('@id'):
					self.data.setdefault('@uri', "%s#%s" % ( self.page_uri, self.data['@id'], ))
				else:
					self.data.setdefault('@uri', self.page_uri)

				## collect parents
				parent_classes = {}
				node = root_element
				while node and node.__class__ != xml.dom.minidom.Document:
					node_classes = node.getAttribute('class')
					if node_classes:
						for node_class in node_classes.split():
							if node_class != self.root_name:
								parent_classes[node_class] = 1

					node = node.parentNode

				parent_classes = parent_classes.keys()
				parent_classes.sort()
				self.data['@parents'] = " ".join(parent_classes)

				spawned = self.Spawn()
				resultd = spawned.data
				resultd.microformat = spawned
				resultd.data = None

				yield	resultd
			except MicroformatInvalid, x:
				Log("stopped processing", text = str(x), exception = True)

		raise StopIteration

	def Feed(self, document, use_tidy = True):
		self.Reset()

		if document.__class__ in [ xml.dom.minidom.Document, xml.dom.minidom.Element ]:
			self.dom = document
			return

		if document.__class__ == self.__class__:
			self.dom = document.dom
			return

		#
		#	Otherwise, we have to parse this
		#
		try:
			self.dom = xml.dom.minidom.parseString(document)
			return
		except UnicodeEncodeError:
			pass

		document = document.encode('utf-8', 'xmlcharrefreplace')

		try:
			self.dom = xml.dom.minidom.parseString(document)
			return
		except xml.parsers.expat.ExpatError:
			if not use_tidy:
				raise

		Log("trying TIDY", verbose = True)
		try:
			( child_stdin, child_stdout ) = os.popen2("tidy -asxml -n -utf8 --repeated-attributes=keep-last -");
			child_stdin.write(document)
			child_stdin.close()

			document = child_stdout.read()
			print document

			try: os.waitpid(-1, os.WNOHANG)
			except: pass
		except IOError, x:
			Log("Alas, no tidy", verbose = True)
			raise	x

		try:
			self.dom = xml.dom.minidom.parseString(document)
		except xml.parsers.expat.ExpatError, x:
			document = document.decode('iso-8859-1', 'replace').encode('ascii', 'xmlcharrefreplace')
			self.dom = xml.dom.minidom.parseString(document)

	def DoIncludePattern(self, root_element):
		include_elements = []

		root_element = root_element.cloneNode(deep = True)

		for element in root_element.getElementsByTagName("*"):
			value = element.getAttribute("class")
			if not value or not "include" in value.split():
				continue

			include_elements.append(element)

		for include_element in include_elements:
			id_name = None
			if include_element.tagName == "object":
				id_name = include_element.getAttribute("data")
			elif include_element.tagName == "a":
				id_name = include_element.getAttribute("href")

			if not id_name or id_name[:1] != '#':
				continue

			id_element = self.id_map.get(id_name[1:])
			if not id_element:
				Log("could not find 'include' element by id", id_name = id_name, ids = self.id_map.keys())
				continue

			id_element = id_element.cloneNode(deep = True)
			include_element.appendChild(id_element)

		return	root_element

	def FeedFile(self, filename):
		try:
			try:
				fin = open(filename, 'rb')
				document = fin.read()
			except:
				Log("cannot read file", filename = filename, exception = True)
				raise

			self.Feed(document)
		finally:
			try: fin.close()
			except: pass


	def PragmaCLI(self, args = None):
		"""Called from the command line"""
		if self.page_uri and not args:
			uri_loader = bm_uri.HTMLLoader(self.page_uri, min_retry = 60)
			uri_loader.Load()

			cooked = uri_loader.GetCooked()
			if not cooked:
				raise	MicroformatError("The HTML document was unparsable", uri = options.page_uri)

			self.Feed(cooked)
		else:
			if args:
				file = args[0]
			else:
				file = "-"

			if file == "-":
				self.Feed(sys.stdin.read())
			else:
				self.FeedFile(file)


	#
	#	This resets any data that has been collected, NOT the rules themselves
	#
	def Reset(self):
		self.root_element = None
		self.intermediates = []
		self.data = uf_mfdict.mfdict()
		self.repeat_count = {}
		self.CustomizeReset()

	def Spawn(self):
		raise	NotImplementedError()

	#
	#
	#
	def Start(self, element):
		Log("Start", classes = element.getAttribute("class").split(), parent = self, verbose = True)
		self.Reset()

		#
		#	id of the root element
		#
		id = element.getAttribute("id")
		if id and id.strip():
			self.data['@id'] = id

		#
		#	weird nesting cases
		#
		parent = element.parentNode
		while parent:
			if hasattr(parent, "getAttribute") and self.root_name in parent.getAttribute("class").split():
				raise	MicroformatInvalid("node already processed")
			else:
				parent = parent.parentNode

		#
		#	process
		#
		self.root_element = element

		for cname in element.getAttribute("class").split():
			self.CookClass(element, cname)

		for rname in element.getAttribute("rel").split():
			self.CookRel(element, rname)

		self.CookTag(element, element.tagName)

	def Add(self, element):
		Log("Add", classes = element.getAttribute("class").split(), verbose = True)

		for cname in element.getAttribute("class").split():
			self.CookClass(element, cname)

		for rname in element.getAttribute("rel").split():
			self.CookRel(element, rname)

		self.CookTag(element, element.tagName)

	def End(self):
		Log("End", verbose = True)

		self.CustomizePreEnd()

		for ( name, element, text ) in self.intermediates:
			modifiers = []

			parent = element
			while parent:
				if hasattr(parent, "MF_PATH"):
					modifiers = parent.MF_PATH + modifiers

				if parent == self.root_element:
					break
				else:
					parent = parent.parentNode

			modifiers = filter(lambda s: s, modifiers)
			modifiers = map(lambda s: s.lower(), modifiers)

			if name:
				name = self.RepeatingName(name)

				if name in modifiers:
					modifiers.remove(name)

				modifiers.append(name)

			self.PutData(u".".join(modifiers), text)

		self.CustomizePostEnd()

	#
	#	Document weirdness
	#
	def AddQuirk(self, quirk):
		self.data[self.RepeatingName("@quirk", force = True)] = quirk

	#
	#	Redefine these in subclasses if you want to muck with
	#	the 'intermediates' or 'data'
	#
	def CustomizeReset(self):
		pass

	def CustomizePreEnd(self):
		pass

	def CustomizePostEnd(self):
		pass

	#
	#	This can be redefined in subclasses to change replacement rules. Try
	#	to call '_PutData' to do the actual work though
	#
	#	The default is "non-replacement" -- once we've seen something it sticks
	#
	def PutData(self, key, value):
		if not self.data.has_key(key):
			self._PutData(key, value)

	def _PutData(self, key, value):
		if key and type(value) in types.StringTypes:
			parts = key.split(".")
			if parts[-1] in self.uris and value:
				if self.page_uri:
					value = urlparse.urljoin(self.page_uri, value)

				try: value = urllib.unquote(value)
				except: pass

			if self.title_class and self.title_class in parts:
				self.data['@title'] = value

			if self.bookmark_class and self.bookmark_class in parts:
				self.data['@uri'] = value

		self.data[key] = value

	#
	#
	#
	def RepeatingName(self, name, force = False):
		if not force and name not in self.repeats:
			return	name

		count = self.repeat_count.get(name, 0)
		self.repeat_count[name] = count + 1

		return	u"%s.%03d" % ( name, count, )

	#
	#	Add a new action -- probably little need to redefine this
	#
	def AddAction(self, name_type, name, action, tuple):
		self.actions.setdefault("%s:%s" % ( name_type, name ), []).append((action, tuple))

	#
	#	These are called from 'Add' to process various types
	#	of elements
	#
	def CookClass(self, element, name):
		self.Cook(element, name, "class")

	def CookRel(self, element, name):
		self.Cook(element, name, "rel")

	def CookTag(self, element, name):
		self.Cook(element, name, "tag")

	def Cook(self, element, name, name_type):
		for ( action, arguments ) in self.actions.get("%s:%s" % ( name_type, name, ), []):
			Log(element = element, name = name, name_type = name_type, action = action, verbose = True)
			action(name, element, *arguments)

	#
	#	Declare a Microformat name that can repeat (i.e. that can have more
	#	than one value). These will be added to the result as "#-name"
	#
	def DeclareRepeatingName(self, name):
		self.repeats.append(name)

	def DeclareURI(self, name):
		self.uris.append(name)

	def DeclareTitle(self, name):
		self.title_class = name

	def DeclareBookmark(self, name):
		"""Bookmarks define the @uri parameter"""
		self.bookmark_class = name

	#
	#	Add ('collect') the text from any XHTML elements
	#	where class="<name>". If 'as_name' is set, you
	#	can force the name to be added as something else.
	#
	def CollectClassText(self, name, as_name = None, text_type = TT_TEXT):
		self.AddAction("class", name, self.DoCollectClassText, ( as_name or name, text_type, ))

	#
	#	Add ('collect') the text from any XHTML elements
	#	where rel="<name>"
	#
	def CollectRelText(self, name, as_name = None, text_type = TT_TEXT):
		self.AddAction("rel", name, self.DoCollectClassText, ( as_name or name, text_type, ))

	def DoCollectClassText(self, name, element, as_name, text_type):	# rename XXX DoCollectText
		Log(name = name, element = element, verbose = True)

		text = ""
		if text_type == TT_TEXT:
			text = self.GetText(element)

			if not text.strip():
				alt = element.getAttribute('alt')
				if alt:
					text = alt
		elif text_type == TT_STRING:
			text = self.GetText(element)
			text = " ".join(text.split())

			if not text.strip():
				alt = element.getAttribute('alt')
				if alt:
					text = alt
		elif text_type == TT_FLOAT:
			value = bm_extract.coerce_float(self.GetText(element), otherwise = None)
			if value != None:
				text = value
		elif text_type == TT_INT:
			value = bm_extract.coerce_int(self.GetText(element), otherwise = None)
			if value != None:
				text = value
		elif text_type == TT_ABBR:
			if element.tagName == 'abbr':
				text = element.getAttribute('title')
			else:
				text = self.GetText(element)
		elif text_type == TT_ABBR_DT:
			import dt

			if element.tagName == 'abbr':
				text = element.getAttribute('title')
			else:
				text = self.GetText(element)

			text = dt.normalize(text)
			if not text:
				return
		elif text_type == TT_XML_OUTER:
			text = element.toxml('utf8').decode('utf8')
		elif text_type == TT_XML_INNER:
			text = u"".join(map(lambda e: e.toxml('utf8').decode('utf8'), element.childNodes)).strip()

		self.AddResult(as_name, element, text)

	#
	#	Add ('collect') the text from any XHTML elements
	#	where class="<name>". If 'as_name' is set, you
	#	can force the name to be added as something else.
	#
	def CollectClassReparse(self, name, reparser, as_name = None):
		self.AddAction("class", name, self.DoCollectClassReparse, ( reparser, as_name or name, ))

	def CollectRelReparse(self, name, reparser, as_name = None):
		self.AddAction("rel", name, self.DoCollectClassReparse, ( reparser, as_name or name, ))

	def DoCollectClassReparse(self, name, element, reparser, as_name):
		Log(name = name, element = element, verbose = True)

		## HACK!
		if type(element) in types.StringTypes:
			text = element
		else:
			text = element.toxml('utf8').decode('utf8')

		try:
			reparser.Feed(text)
		except:
			Log("unparsable XHTML?", xml = text, exception = True)
			return

		#
		#	This bypasses the whole PutData thing and puts
		#	a List of Dictionary to store each result
		#
		collected_list = self.data.setdefault(as_name, [])

		for reparsed in reparser.Iterate():
			collected_list.append(reparsed)

	#
	#	Add ('collect') the text from any XHTML elements
	#	where class="<name>".
	#
	def CollectClassCall(self, name, function, *args):
		self.AddAction("class", name, self.DoClassCall, ( function, args, ))

	def CollectRelCall(self, name, function, *args):
		self.AddAction("rel", name, self.DoClassCall, ( function, args, ))

	def DoClassCall(self, name, element, function, args):
		function(name, element, *args)

	#
	#	Add ('collect') the text from any XHTML elements
	#	where class="<name>". Then add it using the name
	#	of a parent class, restricted by the list 'parent_names'.
	#
	#	This is to deal with hCard's "value" attribute
	#
	def CollectClassTextAsParentName(self, name, parent_names):
		self.AddAction("class", name, self.DoCollectClassTextAsParentName, ( parent_names, ))

	def DoCollectClassTextAsParentName(self, name, element, parent_names):
		Log(name = name, element = element, verbose = True)

		parent = element
		while parent:
			for cname in parent.getAttribute("class").split():
				if cname in parent_names:
					name = cname
					parent = None
					break

			if not parent:
				break
			elif parent == self.root_element:
				break
			else:
				parent = parent.parentNode

		self.AddResult(name, element, self.GetText(element))

	#
	#	Add ('collect') the attribute value from any XHTML elements
	#	where class="<name>"
	#
	def CollectClassAttribute(self, name, attribute):
		self.AddAction("class", name, self.DoCollectClassAttribute, ( attribute, ))

	def DoCollectClassAttribute(self, name, element, attribute):
		Log(name = name, element = element, verbose = True)

		self.AddResult(name, element, element.getAttribute(attribute))

	#
	#	Add ('collect') the attribute value from any XHTML elements
	#	where rel="<name>"
	#
	def CollectRelAttribute(self, name, attribute):
		self.AddAction("rel", name, self.DoCollectRelAttribute, ( attribute, ))

	def DoCollectRelAttribute(self, name, element, attribute):
		Log(name = name, element = element, verbose = True)

		self.AddResult(name, element, element.getAttribute(attribute))

	#
	#	Add ('collect') the text from any XHTML elements
	#	where tagName="<name>"
	#
	def CollectTagText(self, name, as_name = None):
		self.AddAction("tag", name, self.DoCollectTagText, ( as_name or name, ))

	def DoCollectTagText(self, name, element, as_name):
		Log(name = name, element = element, verbose = True)

		self.AddResult(as_name, element, self.GetText(element))

	#
	#	Add ('collect') the text from any XHTML elements
	#	where class="<name>" AND add it to the modifiers
	#	list ON THE PARENT -- i.e. it is modifying siblings
	#
	def CollectClassTextAsModifier(self, name):
		self.AddAction("class", name, self.DoCollectClassTextAsModifier, ())

	def DoCollectClassTextAsModifier(self, name, element):
		Log(name = name, element = element, verbose = True)

		if element.tagName == 'abbr':
			text = element.getAttribute('title')
		else:
			text = self.GetText(element)

		text = self.CustomizeModifier(name, element, text)

		#
		#	Add to the parent
		#
		parent_element = element.parentNode

		if not hasattr(parent_element, "MF_PATH"):
			parent_element.MF_PATH = []

		parent_element.MF_PATH.append(text)

	def CustomizeModifier(self, name, element, modifier_value):
		return	modifier_value

	#
	#	Add ('collect') any XHTML elements where
	#	class="<name>" and then add <name> to the modifiers
	#
	def CollectClassModifier(self, name):
		self.AddAction("class", name, self.DoCollectClassModifier, ())

	def DoCollectClassModifier(self, name, element):
		Log(name = name, element = element, verbose = True)

		if not hasattr(element, "MF_PATH"):
			element.MF_PATH = []
	
		if name not in element.MF_PATH:
			element.MF_PATH.append(name)

	#
	#	Add ('collect') any XHTML elements where
	#	rel="<name>" and then add <name> to the modifiers
	#
	def CollectRelModifier(self, name):
		self.AddAction("rel", name, self.DoCollectRelModifier, ())

	def DoCollectRelModifier(self, name, element):
		Log(name = name, element = element, verbose = True)

		if not hasattr(element, "MF_PATH"):
			element.MF_PATH = []

		element.MF_PATH.append(name)

	#
	#	This adds data to the intermediates; redefine
	#	(and chain) within subclasses if you want to scrub
	#
	def AddResult(self, name, element, text):
		self.intermediates.append((name, element, text))

	#
	#	This will return the text within an element
	#
	def GetText(self, element):
		stack = [ element ]
		result = []

		while stack:
			top_node = stack.pop(0)

			if type(top_node) in types.StringTypes:
				result.append(top_node)
			elif top_node.nodeType == xml.dom.Node.ELEMENT_NODE:
				if top_node.tagName in [ "div", "p", "table", "tr", "td", "h1", "h2", "h3", "h4", "h5", "h6", ]:
					stack = [ "\n" ] + top_node.childNodes + [ "\n" ] + stack
				else:
					stack = top_node.childNodes + stack
			elif top_node.nodeType == xml.dom.Node.TEXT_NODE:
				result.append(top_node.data)

		result = "".join(result)
		result = re.sub("\s*\n+\s*", "\n", result)
		result = re.sub("[ \t]+", " ", result)

		return	result.strip()

	#
	#	This will return a list of all the classes used by
	#	parents of the element, up to and including the root.
	#	The results will be ordered with root last
	#
	def AllParentClass(self, element, include_element = False):
		return	self.AllParent(element, "class", include_element)

	def AllParentRel(self, element, include_element = False):
		return	self.AllParent(element, "rel", include_element)

	def AllParent(self, element, type, include_element = False):
		return	reduce(
			lambda x, y: x + y,
			map(
				lambda element: element.getAttribute(type).split(),
				self.AllParentElements(element, include_element)
			)
		)

	def AllParentTagNames(self, element, include_element = False):
		return	map(
			lambda element: element.tagName,
			self.AllParentElements(element, include_element))

	def AllParentElements(self, element, include_element = False):
		if include_element:
			parent_element = element
		else:
			parent_element = element.parentNode

		elements = []

		while True:
			elements.append(parent_element)

			if parent_element == self.root_element:
				break
			else:
				parent_element = parent_element.parentNode

		return	elements
