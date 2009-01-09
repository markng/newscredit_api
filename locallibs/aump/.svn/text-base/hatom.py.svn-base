#
#	hatom.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
#

import sys

import os
import pprint
import types
import copy
import re
import xml.dom.minidom
import xml.dom

import microformat
import hcard
import reltag
from microformat import Log

scrub_res = [
	"^<div[^/>]*/>\s*",
	"<div[^/>]*/>\s*$",
]

class MicroformatHAtom(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "hentry", uf_name = "hAtom", **args)

		self.CollectClassText('entry-content', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('entry-summary', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('entry-title', text_type = microformat.TT_STRING)
		self.DeclareTitle('entry-title')
		self.CollectRelAttribute('bookmark', 'href')
		self.DeclareBookmark('bookmark')
		self.CollectTagText('h1', 'header')
		self.CollectTagText('h2', 'header')
		self.CollectTagText('h3', 'header')
		self.CollectTagText('h4', 'header')
		self.CollectTagText('h5', 'header')
		self.CollectTagText('h6', 'header')

		self.CollectClassText('updated', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('posted', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('published', text_type = microformat.TT_ABBR_DT)

		self.CollectClassCall('author', self.DoAddress)
		self.DeclareRepeatingName('author')

		self.CollectRelReparse('tag', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))
		self.DeclareRepeatingName('tag')

		self.DeclareURI('bookmark')

	def Spawn(self):
		mf = MicroformatHAtom(page_uri = self.page_uri, parent = self)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def CustomizePostEnd(self):
		if not self.data.has_key('author'):
			found = False
			check_element = self.root_element.parentNode
			while check_element != None and not found:
				hcard_parser = hcard.MicroformatHCard(page_uri = self.page_uri, parent = self)
				hcard_parser.Feed(check_element)

				#
				#	Rules for using the hCard:
				#	- it must be an <address>
				#	- it must have class 'author'
				#	- it must not be in an entry
				#
				for result in hcard_parser.Iterate():
					root_element = result.microformat.root_element

					if root_element.tagName != "address":
						continue

					if not "author" in root_element.getAttribute("class").split():
						continue

					# make sure this isn't in an entry
					in_entry = False

					pe = root_element
					while pe:
						if hasattr(pe, "getAttribute") and "hentry" in pe.getAttribute("class").split():
							in_entry = True
							break

						pe = pe.parentNode

					if in_entry:
						continue

					# keep this hCard (and other's at this level)
					self.data.setdefault("author", []).append(result)
					found = True

				check_element = check_element.parentNode

		if self.data.has_key('header'):
			if not self.data.has_key('entry-title'):
				self.PutData('entry-title', self.data['header'])

			del self.data['header']

		if self.data.has_key('posted'):
			if not self.data.has_key('published'):
				self.data['published'] = self.data['posted']

			del self.data['posted']

		#
		#	If no entry-title and not in hfeed, use title of the page
		#
		if not self.data.has_key('entry-title'):
			found_feed = False
			
			check_element = self.root_element.parentNode
			while check_element != None and check_element != self.dom:
				if "hfeed" in check_element.getAttribute("class").split():
					found_feed = True
					break

				check_element = check_element.parentNode

			if not found_feed:
				titles = self.dom.getElementsByTagName("title")
				if titles:
					text = self.GetText(titles[0])
					text = " ".join(text.split())

					self.PutData('entry-title', text)
					

	#
	#	This allows addresses to be "hCard"s or plain strings
	#	- this is not strictly in compliance with hAtom 0.1, since
	#	we always require hCards
	#
	def DoAddress(self, name, element):
		if "vcard" not in element.getAttribute("class").split():
			text = self.GetText(element)
			self.DoCollectClassReparse(name,
				"<div class='vcard fn'>%s</div>" % text,
				hcard.MicroformatHCard(page_uri = self.page_uri),
				name)
		else:
			self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)

	#
	#	Redefined from microformat.Microformat
	#
	#	The stops nesting of certain elements as per
	#	http://microformats.org/wiki/hatom#Nesting_Rules
	#
	opaque_list = [ "blockquote", "cite", "q" ]

	def AddResult(self, name, element, text):
		if name not in self.opaque_list:
			parent_classes = self.AllParentTagNames(element, include_element = False)
			for opaque in self.opaque_list:
				if opaque in parent_classes:
					return

		microformat.Microformat.AddResult(self, name, element, text)

	#
	#	Redefined from microformat.Microformat
	#
	def PutData(self, key, value):
		if key in [ "entry-content", "entry-summary", ]:
			for scrub_re in scrub_res:
				value = re.sub(scrub_re, "", value)

			if not self.data.has_key(key):
				self._PutData(key, value)
			else:
				self._PutData(key, self.data[key] + "\n" + value)
		else:
			if not self.data.has_key(key):
				self._PutData(key, value)

if __name__ == '__main__':
	import microformat
	microformat.debug = 1

	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--uri",
		default = "",
		dest = "page_uri",
		help = "The URI of the page being processed")
	parser.add_option(
		"", "--verbose",
		default = False,
		action = "store_true",
		dest = "verbose",
		help = "print a lot about what is happening",
	)

	(options, args) = parser.parse_args()
	Log.verbose = options.verbose

	parser = MicroformatHAtom(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
