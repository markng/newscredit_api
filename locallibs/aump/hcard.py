#
#	hcard.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
#

import sys
import urlparse

import os
import pprint
import types
import re
import xml.dom.minidom
import xml.dom
import urllib

import microformat
from microformat import Log

import bm_uri
import bm_validate

not_word_re = "[^\w]"
not_word_rex = re.compile(not_word_re, re.I|re.DOTALL|re.MULTILINE)

class MicroformatHCard(microformat.Microformat):
	def __init__(self, fn2n = True, **args):
		microformat.Microformat.__init__(self, root_name = "vcard", uf_name = "hCard", **args)

		self.fn2n = fn2n
		self.loose_uris = []

		self.CollectClassText('fn', text_type = microformat.TT_STRING)
		self.DeclareTitle('fn')
		self.CollectClassText('family-name', text_type = microformat.TT_STRING)
		self.CollectClassText('given-name', text_type = microformat.TT_STRING)
		self.CollectClassText('additional-name', text_type = microformat.TT_STRING)
		self.CollectClassText('honorific-prefix', text_type = microformat.TT_STRING)
		self.CollectClassText('honorific-suffix', text_type = microformat.TT_STRING)
		self.CollectClassText('nickname', text_type = microformat.TT_STRING)
		self.CollectClassText('sort-string', text_type = microformat.TT_STRING)
		self.CollectClassText('tel', text_type = microformat.TT_STRING)
		self.CollectClassText('post-office-box', text_type = microformat.TT_STRING)
		self.CollectClassText('extended-address', text_type = microformat.TT_STRING)
		self.CollectClassText('street-address', text_type = microformat.TT_STRING)
		self.CollectClassText('locality', text_type = microformat.TT_STRING)
		self.CollectClassText('region', text_type = microformat.TT_STRING)
		self.CollectClassText('postal-code', text_type = microformat.TT_STRING)
		self.CollectClassText('country-name', text_type = microformat.TT_STRING)
		self.CollectClassText('label', text_type = microformat.TT_STRING)
		self.CollectClassText('latitude', text_type = microformat.TT_STRING)
		self.CollectClassText('longitude', text_type = microformat.TT_STRING)
		self.CollectClassText('tz', text_type = microformat.TT_STRING)
		## self.CollectClassText('logo', text_type = microformat.TT_STRING)
		self.CollectClassText('sound', text_type = microformat.TT_STRING)
		self.CollectClassText('title', text_type = microformat.TT_STRING)
		self.CollectClassText('role', text_type = microformat.TT_STRING)
		self.CollectClassText('organization-name', text_type = microformat.TT_STRING)
		self.CollectClassText('organization-unit', text_type = microformat.TT_STRING)
		self.CollectClassText('category', text_type = microformat.TT_STRING)
		self.CollectClassText('note', text_type = microformat.TT_STRING)
		self.CollectClassText('class', text_type = microformat.TT_STRING)
		self.CollectClassText('key', text_type = microformat.TT_STRING)
		self.CollectClassText('mailer', text_type = microformat.TT_STRING)
		self.CollectClassText('uid', text_type = microformat.TT_STRING)
		self.CollectClassText('rev', text_type = microformat.TT_STRING)
		self.CollectClassText('agent', text_type = microformat.TT_STRING)

		self.CollectClassText('bday', text_type = microformat.TT_ABBR_DT)

		self.CollectClassAttribute('url', 'href')
		self.CollectClassAttribute('email', 'href')
		self.CollectClassAttribute('photo', 'src')
		self.CollectClassAttribute('logo', 'src')

		self.CollectClassTextAsParentName('value', [ 'tel', ])

		self.CollectClassTextAsModifier('type')

		self.CollectClassModifier('n')
		self.CollectClassModifier('adr')
		self.CollectClassModifier('geo')
		self.CollectClassModifier('org')
		self.CollectClassModifier('tel')

		self.DeclareURI('url')
		self.DeclareURI('email')
		self.DeclareURI('photo')

		# quirks
		self.CollectClassText('org', as_name = '_org', text_type = microformat.TT_STRING)
		self.CollectClassText('url', as_name = '_url', text_type = microformat.TT_STRING)
		self.CollectClassText('email', as_name = '_email', text_type = microformat.TT_STRING)

	def CookTag(self, element, tagName):
		"""Lose URLs"""
		if tagName != "a":
			return

		href = element.getAttribute('href')
		if href:
			href = urlparse.urljoin(self.page_uri, href)

			try: href = urllib.unquote(href)
			except: pass

			self.loose_uris.append(href)

	def Spawn(self):
		mf = MicroformatHCard(page_uri = self.page_uri)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def CustomizeReset(self):
		self.loose_uris = []

	def CustomizePostEnd(self):
		#
		#	Mostly 'organization-name' is missing so we have to make it up
		#
		okey_2, organization_name_2 = self.data.finditem('org._org')
		if okey_2:
			del self.data[okey_2]

		okey_1, organization_name = self.data.finditem('org.organization-name')
		if not organization_name and organization_name_2:
			self.data[u'org.organization-name'] = organization_name_2
			organization_name = organization_name_2

		#
		#	Quirks
		#
		qkey, qvalue = self.data.finditem('_url')
		if qvalue:
			okey, ovalue = self.data.finditem('url')
			if not ovalue:
				error = bm_validate.validate_uri(qvalue, schemes = [ 'http', 'https', ])
				if error:
					if self.page_uri and self.page_uri.find(qvalue) > -1:
						self.data['url'] = "http://%s/" % qvalue.rstrip('/')
						self.AddQuirk("url as text, and no http:// but matched BASE")
					elif re.search(".+[.](com|org|net|edi|[a-z][a-z])$", qvalue):
						self.data['url'] = "http://%s/" % qvalue.rstrip('/')
						self.AddQuirk("url as text, and no http:// but kinda looks like one")
				else:
					self.data['url'] = qvalue
					self.AddQuirk("url as text")

			try: del self.data[qkey]
			except: pass

		qkey, qvalue = self.data.finditem('_email')
		if qvalue:
			okey, ovalue = self.data.finditem('email')
			if not ovalue:
				self.data['email'] = qvalue
				self.AddQuirk("email as text")

			try: del self.data[qkey]
			except: pass

		#
		#	email
		#
		qkey, qvalue = self.data.finditem('email')
		if qvalue and qvalue.lower().startswith("mailto:"):
			self.data[qkey] = qvalue[7:]

		#
		#	N optimization
		#
		if self.fn2n and self.data.has_key('fn') and self.data.get('fn') != organization_name:
			for key in self.data.keys():
				if key.startswith("n."):
					return

			fn = self.data['fn'].split()

			if fn and fn[0][-1:] == ',':
				fn = fn[1:] + [ fn[0][:-1] ]

			if not fn:
				return

			if fn[0].lower() in [ "mr.", "ms.", "miss", "dr.", "sir", "madam", "m.", "mmes.", ]:
				self.data["n.honorific-prefix"] = fn[0]
				fn = fn[1:]

			if len(fn) == 1:
				self.data["n.given-name"] = fn[0].rstrip(",")
			elif len(fn) == 2:
				self.data["n.given-name"] = fn[0].rstrip(",")
				self.data["n.family-name"] = fn[1].rstrip(",")
			elif len(fn) >= 3:
				self.data["n.given-name"] = fn[0].rstrip(",")
				self.data["n.additional-name"] = fn[1].rstrip(",")
				self.data["n.family-name"] = fn[2].rstrip(",")

				if len(fn) >= 4:
					self.data["n.honorific-suffix"] = fn[3].rstrip(",")

		id = self.root_element.getAttribute("id")
		if id:
			self.data.setdefault('@uri', '%s#%s' % ( self.page_uri, id ))

		if self.data.get('@title') in [ None, "", microformat.NO_TITLE, ]:
			uri = self.data.get('uri')
			if not uri:
				uri = self.page_uri
			if uri:
				self.data['@title'] = bm_uri.trim(uri)

		photo = self.data.find('photo')
		if photo:
			self.data['@photo'] = photo

		#
		#	Loose URLs
		#
		if self.loose_uris:
			for key, value in self.data.iteritems():
				if value in self.loose_uris:
					self.loose_uris.remove(value)

			if self.loose_uris:
				self.data['@loose-uris'] = self.loose_uris

	def CustomizeModifier(self, name, element, modifier_value):
		return	not_word_rex.split(modifier_value.strip().lower())[0]

if __name__ == '__main__':
	import microformat
	import uf_vcard

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
	parser.add_option(
		"", "--scrub",
		default = False,
		action = "store_true",
		dest = "scrub",
		help = "scrub the resulting hCard for nicer/more complete results",
	)

	(options, args) = parser.parse_args()
	Log.verbose = options.verbose

	parser = MicroformatHCard(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		if options.scrub:
			uf_vcard.scrub(resultd)
			
		pprint.pprint(resultd, width = 1)
