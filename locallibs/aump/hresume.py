#
#	hresume.py
#
#	David Janes
#	BlogMatrix
#	2006.09.15
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
import hcalendar
import reltag
from microformat import Log

class MicroformatHResume(microformat.Microformat):
	def __init__(self, **args):
		microformat.Microformat.__init__(self, root_name = "hresume", uf_name = "hResume", include = True, **args)

		self.CollectClassReparse('contact', hcard.MicroformatHCard(page_uri = self.page_uri, parent = self, keep_html = True))

		self.CollectClassReparse('affiliation', hcard.MicroformatHCard(page_uri = self.page_uri, parent = self))
		self.DeclareRepeatingName('affiliation')

		self.CollectClassCall('education', self.ParseExperience)
		self.DeclareRepeatingName('education')

		self.CollectClassCall('experience', self.ParseExperience)
		self.DeclareRepeatingName('experience')

		self.CollectClassReparse('skill', reltag.MicroformatRelTag(page_uri = self.page_uri, parent = self))

		## Quirks mode
		self.CollectClassCall('vcard', self.QuirksVCard)
		self.quirk_vcard = None

	def ParseExperience(self, name, element):
		"""hCalendar extended with hCard for title"""

		## we parse for the dates around the experience
		hcalendar_parser = hcalendar.MicroformatHCalendar(page_uri = self.page_uri, parent = self)
		hcalendar_parser.Feed(element.toxml())
		hcalendar_resultd = None

		for hcalendar_resultd in hcalendar_parser.Iterate():
			break

		# Log(hcalendar_resultd = hcalendar_resultd, e = element.toxml())

		## possible (not likely?) more than one experience
		hcard_parser = hcard.MicroformatHCard(page_uri = self.page_uri, parent = self)
		hcard_parser.Feed(element.toxml())

		for hcard_resultd in hcard_parser.Iterate():
			okey, orgv = hcard_resultd.finditem('organization-name')
			if orgv:
				hcard_resultd['@title'] = orgv

			if hcalendar_resultd:
				okey, orgv = hcalendar_resultd.finditem('dtstart')
				if orgv:
					hcard_resultd['dtstart'] = orgv

				okey, orgv = hcalendar_resultd.finditem('dtend')
				if orgv:
					hcard_resultd['dtend'] = orgv

			self.data.setdefault(name, []).append(hcard_resultd)

	def QuirksVCard(self, name, element):
		class_name = element.getAttribute("class")
		if not class_name:
			return

		if not self.quirk_vcard and class_name == "vcard":
			parser = hcard.MicroformatHCard(page_uri = self.page_uri, parent = self, keep_html = True)
			parser.Feed(element.toxml())

			for result in parser.Iterate():
				self.quirk_vcard = result
				break

	def CustomizePostEnd(self):
		if not self.data.get('contact') and self.quirk_vcard:
			self.data['contact'] = [ self.quirk_vcard ]
			self.AddQuirk("missing-contact")

		contacts = self.data.get('contact')
		if contacts:
			self.data['@title'] = contacts[0].get('@title') or microformat.NO_TITLE

	def Spawn(self):
		mf = MicroformatHResume(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

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

	parser = MicroformatHResume(page_uri = options.uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)
