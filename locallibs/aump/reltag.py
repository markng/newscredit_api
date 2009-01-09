#
#	reltag.py
#
#	David Janes
#	BlogMatrix
#	2005.12.06
#

import sys

import os
import os.path
import pprint
import types
import re
import xml.dom.minidom
import xml.dom
import urllib
import urlparse

from bm_log import Log

import microformat
import hcard
from microformat import Log

class MicroformatRelTag(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "tag", uf_name = "rel-tag", root_type = "rel", **args)

		self.CollectClassText('rating', text_type = microformat.TT_ABBR)
		self.CollectClassText('best', text_type = microformat.TT_ABBR)
		self.CollectClassText('worst', text_type = microformat.TT_ABBR)

		self.CollectRelAttribute('tag', 'href')
		self.CollectRelText('tag', as_name = 'tag-text', text_type = microformat.TT_STRING)
		self.DeclareURI('authority')

		self.DeclareTitle("name")

	def Spawn(self):
		mf = MicroformatRelTag(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def AddResult(self, name, element, text):
		if name == "tag":
			tag_name = os.path.basename(text.rstrip('/'))

			uri = text
			if self.page_uri:
				uri = urlparse.urljoin(self.page_uri, uri)

			microformat.Microformat.AddResult(self, "name", element, urllib.unquote(tag_name))
			microformat.Microformat.AddResult(self, "uri", element, uri)
		else:
			microformat.Microformat.AddResult(self, name, element, text)

	def CustomizePostEnd(self):
		tag = self.data.get('tag-text')
		if tag:
			if not self.data.get('uri'):
				self.data['uri'] = 'http://www.technorati.com/tag/' + urllib.quote(tag, safe = '')
				self.data.setdefault('@quirks', []).append("missing-uri")

			if not self.data.get('name'):
				self.data['name'] = tag
				self.data.setdefault('@quirks', []).append("missing-name")

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

	parser = MicroformatRelTag(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)

