#
#	hslice.py
#
#	David Janes
#	BlogMatrix
#	2008.11.01
#
#	See:
#	- http://msdn.microsoft.com/en-us/library/cc196992(VS.85).aspx
#	- http://msdn.microsoft.com/en-us/library/cc304073(VS.85).aspx
#	- http://www.code-magazine.com/Article.aspx?quickid=0811052
#
#	Notes:
#	- poorly tested (especially TTL): lack of examples?
#	- rel='entry-content' is not implemented yet
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

class MicroformatHSlice(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "hslice", uf_name = "WebSlice", **args)

		self.CollectClassText('entry-content', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('entry-title', text_type = microformat.TT_STRING)
		self.CollectClassText('ttl', text_type = microformat.TT_INT)
		self.DeclareTitle('entry-title')
		self.CollectRelAttribute('feedurl', 'href')
		self.DeclareBookmark('feedurl')
		self.DeclareURI('bookmark')

		self.CollectClassText('endtime', text_type = microformat.TT_ABBR_DT)

		self.CollectRelReparse('tag', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))
		self.DeclareRepeatingName('tag')

	def Spawn(self):
		mf = MicroformatHSlice(page_uri = self.page_uri, parent = self)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def CustomizePostEnd(self):
		if self.data.has_key('posted'):
			if not self.data.has_key('published'):
				self.data['published'] = self.data['posted']

			del self.data['posted']

		if not self.data.has_key('entry-title'):
			self.data['entry-title'] = ''

		if not self.data.has_key('feedurl') and self.data.get('@url'):
			self.data['feedurl'] = self.data['@url'] 
					
		## this will always happen
		if not self.data.has_key('id') and self.data.get('@id'):
			self.data['id'] = self.data['@id'] 
					

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
	#	http://microformats.org/wiki/hslice#Nesting_Rules
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
		if key in [ "entry-content", ]:
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

	parser = MicroformatHSlice(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
