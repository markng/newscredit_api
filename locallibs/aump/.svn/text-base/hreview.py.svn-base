#
#	hreview.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
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

class MicroformatHReview(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "hreview", uf_name = "hReview", **args)

		self.CollectClassText('version')
		self.CollectClassText('summary', text_type = microformat.TT_STRING)
		self.DeclareTitle('summary')
		self.CollectClassText('description', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('type')
		self.CollectClassText('dtreviewed', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('info', text_type = microformat.TT_XML_OUTER)
		self.CollectClassText('reviewer', text_type = microformat.TT_XML_OUTER)
		self.CollectRelAttribute('permalink', 'href')

		self.CollectClassText('rating', text_type = microformat.TT_ABBR)
		self.CollectClassText('best', text_type = microformat.TT_ABBR)
		self.CollectClassText('worst', text_type = microformat.TT_ABBR)

		self.CollectClassCall('item', self.DoItem)
		self.CollectClassCall('reviewer', self.DoReviewer)

		self.CollectRelReparse('tag', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))

		self.DeclareURI('permalink')

	def Spawn(self):
		mf = MicroformatHReview(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def DoItem(self, name, element):
		if "vcard" not in element.getAttribute("class").split():
			self.DoCollectClassReparse(name, "<div class='vcard'>%s</div>" % element.toxml(),
				hcard.MicroformatHCard(fn2n = False, page_uri = self.page_uri), name)
		else:
			self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)

	def DoReviewer(self, name, element):
		if "vcard" not in element.getAttribute("class").split():
			if self.GetText(element).lower().startswith("anonymous"):
				self.AddResult("reviewer.anonymous", element, "anonymous")
			else:
				self.DoCollectClassReparse(name, "<div class='vcard'>%s</div>" % element.toxml(),
					hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)
		else:
			self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri, parent = self), name)

	#
	#	Redefined from microformat.Microformat
	#
	#	We ignore certain items already processed by the reviewed-tag uF
	#
	def AddResult(self, name, element, text):
		if name in [ "best", "worst", "rating", ]:
			parents = self.AllParentRel(element)
			if "tag" in parents:
				return

		microformat.Microformat.AddResult(self, name, element, text)

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

	parser = MicroformatHReview(page_uri = options.uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
