#
#	xfolk.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
#

import os
import pprint
import types
import re
import xml.dom.minidom
import xml.dom

import sys
#sys.path.insert(0, os.path.join(os.getenv("BM_IROOT"), "blogmatrix/common"))

from bm_log import Log

import microformat
import reltag
from microformat import Log

class MicroformatXFolk(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "xfolkentry", uf_name = "xFolk", **args)

		self.CollectClassText('extended', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('description', text_type = microformat.TT_XML_INNER)
		self.CollectClassText('title')

		self.CollectRelAttribute('taggedlink', 'href')
		self.CollectRelText('taggedlink', as_name = 'title')
		self.CollectClassAttribute('taggedlink', 'href')
		self.CollectClassText('taggedlink', as_name = 'title')

		self.CollectTagText('h1', 'header')
		self.CollectTagText('h2', 'header')
		self.CollectTagText('h3', 'header')
		self.CollectTagText('h4', 'header')
		self.CollectTagText('h5', 'header')
		self.CollectTagText('h6', 'header')

		self.CollectRelReparse('tag', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))
		self.DeclareRepeatingName('tag')
		self.DeclareURI('taggedlink')

	def Spawn(self):
		mf = MicroformatXFolk(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def CustomizePostEnd(self):
		if self.data.has_key('header'):
			if not self.data.has_key('title'):
				self.data['title'] = self.data['header']

			del self.data['header']

		self.data['title'] = " ".join(self.data.get('title', '').split())

		if self.data.has_key('extended'):
			if not self.data.has_key('description'):
				self.data['description'] = self.data['extended']

			del self.data['extended']

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

	parser = MicroformatXFolk(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
