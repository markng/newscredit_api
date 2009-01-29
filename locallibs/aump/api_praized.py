#
#   api_praized.py
#
#   David Janes
#   2008.11.12
#
#	Copyright 2008 David Janes
#
#	Interface to Praized business lookup
#

import os
import sys
import urllib
import types
import pprint
import types

import bm_extract
import bm_uri
import bm_api
import bm_cfg

import uf_mfdict
import uf_vcard
import hcard

class PraizedMerchants(bm_api.APIReader):
	"""See: http://code.google.com/p/praized/wiki/A_Second_Tutorial_Search

	Individual entries look like this:
	{
	 "@Index": 0, 
	 "@Page": 1, 
	 "pid": "af5bebd604f3d1517a8113e0a2e8cc58", 
	 "name": "Coffee Supreme Bistro", 
	 "phone": "(416) 585-7896", 
	 "location": {
	  "city": {
	   "name": "Toronto"
	  }, 
	  "country": {
	   "code": "CA", 
	   "name_fr": "Canada", 
	   "name": "Canada"
	  }, 
	  "longitude": "-79.384071", 
	  "regions": {
	   "province": "Ontario"
	  }, 
	  "postal_code": "M5J 1T1", 
	  "latitude": "43.646347", 
	  "street_address": "40 University Avenue"
	 },
	 "tags": {
	  "tag": [
	   { "name": "coffee" }, 
	   { "name": "houses" }, 
	   { "name": "cafes" }, 
	   { "name": "terrasses" }
	  ]
	 }, 
	 "short_url": "http://przd.com/zAU-7", 
	 "updated_at": "2008-10-04T20:49:34Z", 
	 "tag_count": "4", 
	 "favorite_count": "0", 
	 "permalink": "http://code.davidjanes.com/praized/places/ca/ontario/toronto/coffee-supreme-bistro?l=Toronto&q=Bistro", 
	 "created_at": "2008-10-04T20:49:34Z", 
	 "comment_count": "0", 
	 "votes": {
	  "count": "0", 
	  "pos_count": "0", 
	  "score": "0", 
	  "neg_count": "0"
	 }, 
	 "stat_links": {
	  "stat_link": {
	   "url": "http://ca.stats.praized.com/ping?t=1226583388.14549"
	  }
	 }
	}
	"""

	_meta_path = "community"
	_item_path = "merchants.merchant"
	_page_max_path = 'pagination.page_count'
	_page_max = -1
	_slug = None
	_atom_item = {
		"title" : "name", 
		"id" : "pid", 
		"link" : "permalink", 
	}

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def CustomizePageURI(self, page_index):
		if page_index > 1:
			return	"page=%s" % page_index

	def CustomizeRestart(self):
		if not self._slug:
			self.slug = bm_cfg.cfg.as_string('praized.api_slug')

		if not self._request_meta.get('api_key'):
			self._request_meta['api_key'] = bm_cfg.cfg.as_string('praized.api_key')

	def CustomizeAtomItem(self, d):
		d = bm_api.APIReader.CustomizeAtomItem(self, d)

		#
		#	Tags become categories
		#
		cats = []

		for tag in bm_extract.as_list(d, "tags.tag"):
			cats.append({
				"term" : tag["name"]
			})

		d["category"] = cats

		#
		#	Geolocation
		#
		bm_api.add_latlon(d, bm_extract.as_string(d, "location.latitude"), bm_extract.as_string(d, "location.longitude"))

		#
		#	hcard
		#
		hd = uf_mfdict.mfdict()
		for k_from, k_to in [
			( "location.country.name", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.CountryName, ), ),
			( "location.streetAddress", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.StreetAddress, ), ),
			( "location.city.name", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.Locality, ), ),
			( "location.regions.province", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.Region, ), ),
			( "location.postal_code", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.PostalCode, ), ),
			( "phone", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.TEL, uf_vcard.Voice, ), ),
			( "title", uf_vcard.OrganizationName, ),
			( "location.latitude", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Latitude, ), ),
			( "location.longitude", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Longitude, ), ),
		]:
			try:
				value = bm_extract.as_string(d, k_from)
				if value:
					hd[k_to] = value
			except KeyError:
				pass

		if hd:
			d["hcard:hcard"] = hcard.decompose(hd, "hcard")

		#
		#	Links
		#
		try:
			alt = d.pop("short_url")
			if alt:
				d["links"] = [
					{
						"type" : "text/html",
						"rel" : "alternate",
						"href" : alt,
					},
				]
		except KeyError:
			pass

		#
		#	Removables
		#
		for key in [ "tags", "tag_count", "location", "phone", ]:
			try: del d[key]
			except KeyError: pass

		return	d

	@apply
	def slug():
		def fset(self, slug):
			self._slug = slug
			self._uri_base = "http://api.praized.com/%s/merchants.xml" % self._slug

		return property(**locals())

if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	try:
		import json
	except:
		import simplejson as json

	from bm_log import Log
	Log.verbose = True

	api = PraizedMerchants()
	api.SetRequest(
		q = "Mela",
		l = "Toronto",
	)
	for item in api.items:
		pprint.pprint(item)
