#
#   api_geocode.py
#
#   David Janes
#   2008.11.22
#
#	Copyright 2008 David Janes
#
#	Interface to Google AJAX API
#

import sys
import os
import urllib
import types
import pprint
import types
import socket

try:
	import json
except:
	import simplejson as json

import bm_extract
import bm_uri
import bm_api
import bm_work
import bm_cfg
import uf_vcard
import uf_mfdict
import hcard

from bm_log import Log

class Google(bm_api.APIReader):
	"""
	See: http://code.google.com/apis/ajaxsearch/documentation/reference.html#_intro_fonje
	"""

	_item_path = "responseData.results"
	_meta_path = "responseData.cursor"
	_convert2work = bm_work.JSON2WORK()
	_required_attributes = [ "q" ]
	_page_max = -1

	_atom_item = {
		"titleFormatted" : "title", 
		"title" : "titleNoFormatting", 
		"link" : "url", 
	}

	def __init__(self, **ad):
		ad['v'] = "1.0"
		ad['rsz'] = "large"
		ad.setdefault('_http_referer', 'http://%s' % socket.gethostname())

		bm_api.APIReader.__init__(self, **ad)

	def CustomizePageURI(self, page_index):
		if page_index > 1:
			return	"start=%s" % ( page_index * 8 )

	def CustomizeAtomItem(self, d):
		d = bm_api.APIReader.CustomizeAtomItem(self, d)

		googled = {}
		for key in [ 'ddUrl', 'ddUrlFromHere', 'ddUrlToHere', "addressLines", "accuracy", "listingType", "GsearchResultClass", "titleFormatted", "viewportmode", ]:
			try: googled[key] = d.pop(key)
			except KeyError: pass

		if googled:
			d["gsearch:gsearch"] = googled

		return	d

class WebSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/web"

class LocalSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/local"

	def CustomizeAtomItem(self, d):
		d = Google.CustomizeAtomItem(self, d)
		
		#
		#	Build a hCard from the data
		#	... should add lat/lon here?
		#
		hd = uf_mfdict.mfdict()
		for k_from, k_to in [
			( "country", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.CountryName, ), ),
			( "streetAddress", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.StreetAddress, ), ),
			( "city", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.Locality, ), ),
			( "region", "%s.%s.%s" % ( uf_vcard.Work, uf_vcard.ADR, uf_vcard.Region, ), ),
			( "staticMapUrl", "%s" % ( uf_vcard.Photo, ), ),
			( "title", uf_vcard.OrganizationName, ),
			( "lat", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Latitude, ), ),
			( "lng", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Longitude, ), ),
		]:
			try:
				value = bm_extract.as_string(d, k_from)
				if value:
					hd[k_to] = value
			except KeyError:
				pass

		for pd in bm_extract.as_list(d, "phoneNumbers"):
			number = bm_extract.as_string(pd, "number")
			if not number:
				continue

			type = bm_extract.as_string(pd, "type")

			if type in [ "main", "" ]:
				hd["%s.%s.%s" % ( uf_vcard.TEL, uf_vcard.Voice, uf_vcard.Work, )] = number
			elif type in [ "fax", "data", ]:
				hd["%s.%s.%s" % ( uf_vcard.TEL, uf_vcard.Fax, uf_vcard.Work, )] = number
			elif type == "mobile":
				hd["%s.%s.%s" % ( uf_vcard.TEL, uf_vcard.Mobile, uf_vcard.Work, )] = number
			else:
				hd["%s.%s.%s" % ( uf_vcard.TEL, uf_vcard.Voice, uf_vcard.Work, )] = number

		if hd:
			d["hcard:hcard"] = hcard.decompose(hd, "hcard")

		#
		#
		#
		try:
			bm_api.add_latlon(d, d.pop("lat"), d.pop("lng"), )
		except KeyError:
			pass

		#
		#	Remove stuff
		#
		for key in [ "country", "streetAddress", "city", "region", "staticMapUrl", "phoneNumbers", ]:
			try:
				del d[key]
			except KeyError:
				pass

		#
		#	The result
		#
		return	d

	
class VideoSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/video"
	
class BlogSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/blog"
	
class NewsSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/news"
	
class BookSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/book"
	
class ImageSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/image"
	
class PatentSearch(Google):
	_uri_base = "http://ajax.googleapis.com/ajax/services/search/patentNew"
	
if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	## api_key = bm_cfg.cfg.as_string('google_maps.api_key')
	## referer = "http://code.davidjanes.com"
	query = "Paris Hilton"
	search = "web"

	query = "Bistro on Avenue"
	query = "CIBC"
	search = "local"

	Log.verbose = True

	bm_api.atom_like = True

	if search == "web":
		api = WebSearch(q = query)
	elif search == "local":
		api = LocalSearch(q = query, sll = "43.4,-79.23")
	elif search == "video":
		api = VideoSearch(q = query)
	elif search == "blog":
		api = BlogSearch(q = query)
	elif search == "news":
		api = NewsSearch(q = query)
	elif search == "book":
		api = BookSearch(q = query)
	elif search == "image":
		api = ImageSearch(q = query)
	elif search == "patent":
		api = PatentSearch(q = query)

	for item in api.items:
		pprint.pprint(item)
