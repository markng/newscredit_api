#
#	hcalendar.py
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
from microformat import Log

class MicroformatHCalendar(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "vevent", uf_name = "hCalendar", root_type = "class", collect_ids = True, **args)

		self.CollectClassText('summary', text_type = microformat.TT_STRING)
		self.DeclareTitle('summary')
		self.CollectClassCall('location', self.DoLocation)

		self.CollectClassText('dtstart', text_type = microformat.TT_ABBR_DT)
		self.CollectClassText('dtend', text_type = microformat.TT_ABBR_DT)

		self.CollectClassAttribute('url', 'href')

		self.CollectRelReparse('vcard', hcard.MicroformatHCard(page_uri = self.page_uri, parent = self))

		self.DeclareURI('url')
		self.DeclareBookmark('url')

	def Spawn(self):
		mf = MicroformatHCalendar(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	#
	#	This allows addresses to be "hCard"s or plain strings
	#
	def DoLocation(self, name, element):
		if "vcard" not in element.getAttribute("class").split():
			self.AddResult(name, element, self.GetText(element))
		else:
			self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri), name)

	#
	#	Pre processing for tables
	#
	def CustomizePreEnd(self):
		if self.root_element.tagName != "td":
			return

		headers = self.root_element.getAttribute("headers").split()
		for header in headers:
			header_element = self.id_map.get(header)
			if not header_element:
				continue

			for child_element in header_element.getElementsByTagName("*"):
				self.Add(child_element)

	def CustomizePostEnd(self):
		id = self.root_element.getAttribute("id")
		if id:
			self.data.setdefault('@uri', '%s#%s' % ( self.page_uri, id ))

		#
		#	duration, in hours:minutes:seconds
		#
		try:
			import bm_date

			dt_start = self.data.get("dtstart")
			dt_end = self.data.get("dtend")
			if dt_start and dt_end:
				duration = bm_date.DateHelper(dt_end).datetime() - bm_date.DateHelper(dt_start).datetime()
				self.data["@duration"] = "%02d:%02d:%02d" % (
					duration.days * 24 + duration.seconds // ( 3600 * 24 ),
					duration.seconds // 3600 % 24,
					duration.seconds % 60,
				)
			else:
				self.data["@duration"] = "00:00:00"
		except ImportError:
			pass

	#
	#	Redefined from microformat.Microformat
	#
	def AddResult(self, name, element, text):
		if name in [ "url", ]:
			parents = self.AllParentRel(element)
			if "vcard" in parents:
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

	parser = MicroformatHCalendar(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)

