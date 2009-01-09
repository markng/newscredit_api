#
#	hlisting.py
#
#	David Janes
#	BlogMatrix
#	2006.09.17
#

import sys

import os
import os.path
import pprint
import types
import re
import xml.dom.minidom
import xml.dom

import microformat
import hcard
import reltag
from microformat import Log

class MicroformatHListing(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "hlisting", uf_name = "hListing", **args)

		self.CollectClassText('version')
		self.CollectClassText('summary', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('description', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('type')
		self.CollectClassText('dtlisted', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('dtexpired', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('price', text_type = microformat.TT_STRING)
		self.CollectRelAttribute('permalink', 'href')

		self.CollectClassText('summary', text_type = microformat.TT_STRING, as_name = "_title")
		self.DeclareTitle('_title')

		self.CollectRelReparse('location', hcard.MicroformatHCard(page_uri = self.page_uri, parent = self))

		self.CollectClassCall('item', self.DoItemOrInfo)
		self.CollectClassCall('info', self.DoItemOrInfo)
		self.CollectClassCall('lister', self.DoReviewer)

		self.CollectRelReparse('tag', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))

		self.DeclareURI('permalink')

	def CustomizePostEnd(self):
		if self.data.get('@title') in [ None, "", microformat.NO_TITLE, ]:
			item = self.data.get('item')
			if item:
				self.data['@title'] = item[0].get('@title', microformat.NO_TITLE)

		try: del self.data['_summary']
		except: pass

	def Spawn(self):
		mf = MicroformatHListing(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def DoItemOrInfo(self, name, element):
		hcard_parser = hcard.MicroformatHCard(page_uri = self.page_uri, parent = self, fn2n = False)
		if "vcard" not in element.getAttribute("class").split():
			hcard_parser.Feed("<div class='vcard'>%s</div>" % element.toxml())
		else:
			hcard_parser.Feed(element)

		for hcard_resultd in hcard_parser.Iterate():
			key, value = hcard_resultd.finditem('fn')
			if not value:
				continue

			self.data.setdefault(name, []).append(hcard_resultd)

	def DoReviewer(self, name, element):
		if "vcard" not in element.getAttribute("class").split():
			if self.GetText(element).lower().startswith("anonymous"):
				self.AddResult("lister.anonymous", element, "anonymous")
			else:
				self.DoCollectClassReparse(name, "<div class='vcard'>%s</div>" % element.toxml(),
					hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)
		else:
			self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)

if __name__ == '__main__':
	import microformat
	microformat.debug = 1

	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--uri",
		default = "",
		dest = "uri",
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

	parser = MicroformatHListing(page_uri = options.uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
