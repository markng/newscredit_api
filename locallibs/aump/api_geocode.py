#
#   api_geocode.py
#
#   David Janes
#   2008.11.22
#
#	Copyright 2008 David Janes
#
#	Interface to Geocoders
#

import string
import pprint
import os

import bm_work
import bm_uri
import bm_extract
import bm_cfg
import djolt

from bm_log import Log

import bm_api
import api_google

try:
	import json
except:
	import simplejson as json

class Geocoder(bm_api.APIReader):
	"""Geocode WORK-like dictionaries"""

	_properties = [ "items", ]
	pd = {
		"latitude" : "geo.latitude",
		"longitude" : "geo.longitude",
	}

	def __init__(self, address_geocoder = None, **ad):
		self.address_geocoder = address_geocoder

		bm_api.APIReader.__init__(self, **ad)

	def GetMeta(self):
		return	{}

	def IterItems(self):
		"""See bm_api.IterItems"""

		for item in self._request_items or []:
			self.GeocodeItem(item)
			yield	item

	def Restart(self):
		bm_api.APIReader.Restart(self)

		if not self.address_geocoder:
			self.address_geocoder = GoogleAddressGeocoder(
				api_key = bm_cfg.cfg.as_string('google_maps.api_key'),
				referer = "http://code.davidjanes.com",
			)

	def IterGeocode(self, items):
		"""Iterate through the items, calling and yielding self.Geocode"""

		if not isinstance(items, list):
			items = [ items ]

		for item in items:
			self.GeocodeItem(item)
			yield	item

	def GeocodeItem(self, item):
		"""Geocode a single WORK item, writing in the lat/lon

		Lat/Lon is written in depending on the path values
		for 'latitude' and 'longitude' in self.pd
		"""

		ll = self.GeocodeToLatLon(item)
		if ll:
			bm_extract.set(item, self.pd['latitude'], ll[0])
			bm_extract.set(item, self.pd['longitude'], ll[1])

		return	item

	def GeocodeToLatLon(self, item):
		"""Geocode a single item, returning a lat/lon tuple"""

		address = self._Value(item, key = "address")
		if not address:
			parts = [
				self._Value(item, key = "street_address"),
				self._Value(item, key = "locality"),
				self._Value(item, key = "region"),
				self._Value(item, key = "country_name"),
			]
			parts = filter(None, parts)
			address = ", ".join(parts)

		if address:
			Log("Geocode", address = address, item = item, _request_meta = self._request_meta, pd = self.pd, verbose = True)

			ll = self.address_geocoder.Geocode(address)
			if ll:
				return	ll

	def _Value(self, item, key):
		v = self._request_meta.get(key)
		if not v:
			return	None

		return	djolt.Template(v).render(item)

class AbstractAddressGeocoder:
	"""Geocode an API using an address (i.e. a single string)."""

	def IterGeocode(self, address):
		"""Iterate through all geocoding results for 'address'
		Results are lat/lon tuples.
		"""

		raise	NotImplementedError

	def Geocode(self, address):
		"""Return the first lat/lon geocoding result for address (or None)"""

		raise	NotImplementedError

class GoogleAddressGeocoder(AbstractAddressGeocoder):
	def __init__(self, api_key, referer):
		self.api = api_google.Google(
			key = api_key, 
			_http_referer = referer,
			_http_ad = {
				"min_retry" : 60 * 60 * 24,
			},
		)

	def IterGeocode(self, address):
		self.api.LocalSearch(address)
			
		for llitem in self.api.IterItems():
			lat = bm_extract.as_float(llitem, 'lat', otherwise = None)
			lng = bm_extract.as_float(llitem, 'lng', otherwise = None)

			if lat != None and lng != None :
				yield	( lat, lng )

	def Geocode(self, address):
		for ll in self.IterGeocode(address):
			return	ll

if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	items = [
		{
			"address" : {
				"Street" : "310 Lawrence Avenue West",
				"City" : "North York",
			},
		},
	]

	def demonstrate_local(items):
		import api_google

		geocoder = Geocoder(
			address_geocoder = GoogleAddressGeocoder(
				api_key = bm_cfg.cfg.as_string('google_maps.api_key'),
				referer = "http://code.davidjanes.com",
			),
			street_address = "{{ address.Street }}",
			locality = """{{ address.City|otherwise:"Toronto"}}""",
			region = """{{ address.Province|otherwise:"Ontario"}}""",
			country_name = """{{ address.Country|otherwise:"Canada" }}""",
		)
		for item in geocoder.IterGeocode(items):
			pprint.pprint(item)

	def demonstrate_api(items):
		import api_google

		geocoder = Geocoder()
		geocoder.request = {
			"street_address" : "{{ address.Street }}",
			"locality" : """{{ address.City|otherwise:"Toronto"}}""",
			"region" : """{{ address.Province|otherwise:"Ontario"}}""",
			"country_name" : """{{ address.Country|otherwise:"Canada" }}""",
			"items" : items,
		}
		for item in geocoder.items:
			pprint.pprint(item)

	Log.verbose = False
	## demonstrate_local(items)
	demonstrate_api(items)
