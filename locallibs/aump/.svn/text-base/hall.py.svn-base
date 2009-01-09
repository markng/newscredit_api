#
#	hall.py
#
#	David Janes
#	BlogMatrix
#	2006.09.09
#

import sys

import os
import pprint
import types
import re

import bm_uri
import microformat
from bm_log import Log

import hatom
import hcalendar
import hcard
import hreview
import reltag
import xfolk
import hdocument
import hresume
import hlisting

ufpd = {
	"hresume" : hresume.MicroformatHResume,
	"hlisting" : hlisting.MicroformatHListing,
	"hatom" : hatom.MicroformatHAtom,
	"hcalendar" : hcalendar.MicroformatHCalendar,
	"hcal" : hcalendar.MicroformatHCalendar,
	"vcalendar" : hcalendar.MicroformatHCalendar,
	"vcal" : hcalendar.MicroformatHCalendar,
	"hcard" : hcard.MicroformatHCard,
	"vcard" : hcard.MicroformatHCard,
	"hreview" : hreview.MicroformatHReview,
	"reltag" : reltag.MicroformatRelTag,
	"rel-tag" : reltag.MicroformatRelTag,
	"xfolk" : xfolk.MicroformatXFolk,
	"doc" : hdocument.MicroformatDocument,
	"document" : hdocument.MicroformatDocument,
}

DEFAULT_UFS = [ "hatom", "hcalendar", "hcard", "xfolk", ]

class MicroformatAll:
	"""Get all the microformats on a page (from a subset of all available ufs, obviously!)
	"""
	def __init__(self, uri, ufs = DEFAULT_UFS):
		self.uri = uri
		self.ufs = list(ufs)
		self.ufps = []
		self.resultd = {}

		for uf_name in self.ufs:
			ufp = ufpd.get(uf_name.lower())
			if not ufp:
				raise	microformat.MicroformatError("microformat '%s' not found" % uf_name)

			ufp.all_uf_name = uf_name
			self.ufps.append(ufp)

	def Parse(self):
		uri_loader = bm_uri.HTMLLoader(self.uri)
		uri_loader.Load()

		cooked = uri_loader.GetCooked()
		if not cooked:
			raise	microformat.MicroformatError("The HTML document was unparsable")

		dom = None

		for ufp in self.ufps:
			parser = ufp(page_uri = self.uri)

			try:
				if dom:
					parser.Feed(dom, use_tidy = False)
				else:
					parser.Feed(cooked)
					dom = parser.dom

				results = []
				for item in parser.Iterate():
					results.append(item)

				self.resultd[parser.all_uf_name] = results
			except:
				Log(exception = True, page_uri = self.uri)
				self.resultd[parser.all_uf_name] = []

		return	self.resultd

if __name__ == '__main__':
	import microformat
	microformat.debug = 1

	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--uri",
		default = "",
		dest = "uri",
		help = "load this page and look for microformats",
	)
	parser.add_option(
		"", "--uf",
		action = "append",
		dest = "ufs",
		help = "look for this microformat (hatom|hcalendar|hcard|hreview|rel-tag|xfolk)*. repeats; comma separated ok too.",
	)
	parser.add_option(
		"", "--verbose",
		default = False,
		action = "store_true",
		dest = "verbose",
		help = "print a lot about what is happening",
	)
	parser.add_option(
		"", "--xhtml",
		default = False,
		action = "store_true",
		dest = "xhtml",
		help = "just print out XHTML document",
	)

	(options, args) = parser.parse_args()
	Log.verbose = options.verbose

	if not options.uri:
		print >> sys.stderr, "--uri=URI required"
		parser.print_help(sys.stderr)
		sys.exit(1)

	if not options.ufs:
		ufs = DEFAULT_UFS
	else:
		ufs = []
		for uf in options.ufs:
			ufs += uf.split(",")

	try:
		if options.xhtml:
			uri_loader = bm_uri.HTMLLoader(options.uri, min_retry = 0)
			uri_loader.Load()

			cooked = uri_loader.GetCooked()
			if not cooked:
				raise	microformat.MicroformatError("The HTML document was unparsable", uri = options.uri)
			else:
				print cooked.encode('utf-8')

			sys.exit(0)

		uf_parser = MicroformatAll(uri = options.uri, ufs = ufs)
		resultd = uf_parser.Parse()

		pprint.pprint(resultd)
	except SystemExit:
		raise
	except:
		Log(exception = True)
		parser.print_help(sys.stderr)
		sys.exit(1)
