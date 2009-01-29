#
#   api_foaf.py
#
#   David Janes
#   2009.01.28
#
#	Copyright 2009 David Janes
#
#	Interface to FOAF (RDF)
#
#	You may need to:
#	$ easy_install -U 'rdflib<3a'
#


import sys
import os
import os.path
import re
import time
import types
import urllib
import urlparse
import sets
import pprint
import cStringIO as StringIO

try:
	from rdflib.Graph import Graph
	from rdflib import Namespace
	import rdflib

	if not 'query' in dir(Graph):
		raise	ImportError, "old version"
except ImportError:
	Graph = None

import bm_uri
import bm_extract
import bm_api

import uf_vcard
import uf_mfdict
import hcard

from bm_log import Log

class FOAF(bm_api.APIBase):
	initNs = {
		"foaf" : Namespace("http://xmlns.com/foaf/0.1/"),
		"rdfs" : Namespace("http://www.w3.org/2000/01/rdf-schema#"),
		"con" : Namespace("http://www.w3.org/2000/10/swap/pim/contact#"),
		"geo" : Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#"),
	};

	me = True
	contacts = True

	def IterItems(self):
		self.Produced()

		try:
			loader = bm_uri.URILoader(self.uri)

			graph = Graph()
			graph.parse(StringIO.StringIO(loader.Load()), format = "xml")
		except Exception, x:
			Log(exception = True)
			raise	StopIteration

		if self.me:
			yield self._Profile(graph)

		if self.contacts:
			for item in self._Contacts(graph):
				yield	item

	def _Profile(self, graph):
		query_profile = """
		SELECT
			?name ?nick ?img ?image ?weblog ?page ?profile ?homepage ?mbox_sha1sum
			?locality ?country_name ?postal_code ?street_address ?extended_address
			?phone
			?lat ?lng
		WHERE {
			?a foaf:knows ?b
		.	OPTIONAL { ?a foaf:name ?name }
		.	OPTIONAL { ?a foaf:nick ?nick }
		.	OPTIONAL { ?a foaf:img ?img }
		.	OPTIONAL { ?a foaf:image ?image }
		.	OPTIONAL { ?a foaf:weblog ?weblog }
		.	OPTIONAL { ?a foaf:page ?page }
		.	OPTIONAL { ?a foaf:profile ?profile }
		.	OPTIONAL { ?a foaf:homepage ?homepage }
		.	OPTIONAL { ?a foaf:mbox_sha1sum ?mbox_sha1sum }
		.	OPTIONAL { ?a con:office ?office . ?office con:address ?address . ?address con:city ?locality }
		.	OPTIONAL { ?a con:office ?office1 . ?office1 con:address ?address1 . ?address1 con:country ?country_name }
		.	OPTIONAL { ?a con:office ?office2 . ?office2 con:address ?address2 . ?address2 con:postalCode ?postal_code }
		.	OPTIONAL { ?a con:office ?office3 . ?office3 con:address ?address3 . ?address3 con:street ?street_address }
		.	OPTIONAL { ?a con:office ?office4 . ?office4 con:address ?address4 . ?address4 con:street2 ?extended_address }
		.	OPTIONAL { ?a con:office ?office5 . ?office5 con:phone ?phone }
		.	OPTIONAL { ?a con:office ?office6 . ?office6 geo:lat ?lat }
		.	OPTIONAL { ?a con:office ?office7 . ?office7 geo:long ?lng }
		}"""


		for row in graph.query(query_profile, initNs = self.initNs):
			rd = self._Valued(graph, row, [ 
				"name", "nick", "img", "image", "weblog", "page", "profile", "homepage", "mbox_sha1sum", 
				"locality", "country_name", "postal_code", "street_address", "extended_address",
				"phone",
				"lat", "lng",
			])

			return	self._ProcessRow(rd, uri = self.uri, rel = "me")

	def _Contacts(self, graph):
		try:
			query_foaf = """
SELECT
	?bfoaf
	?name ?nick ?img ?image ?weblog ?page ?profile ?homepage ?mbox_sha1sum
	?locality ?country_name ?postal_code ?street_address ?extended_address
	?phone
	?lat ?lng
WHERE {
	?a foaf:knows ?b
.	?b rdfs:seeAlso ?bfoaf
.	OPTIONAL { ?b foaf:name ?name }
.	OPTIONAL { ?b foaf:nick ?nick }
.	OPTIONAL { ?b foaf:img ?img }
.	OPTIONAL { ?b foaf:image ?image }
.	OPTIONAL { ?b foaf:weblog ?weblog }
.	OPTIONAL { ?b foaf:page ?page }
.	OPTIONAL { ?b foaf:profile ?profile }
.	OPTIONAL { ?b foaf:homepage ?homepage }
.	OPTIONAL { ?b foaf:mbox_sha1sum ?mbox_sha1sum }
.	OPTIONAL { ?b con:office ?office . ?office con:address ?address . ?address con:city ?locality }
.	OPTIONAL { ?b con:office ?office1 . ?office1 con:address ?address1 . ?address1 con:country ?country_name }
.	OPTIONAL { ?b con:office ?office2 . ?office2 con:address ?address2 . ?address2 con:postalCode ?postal_code }
.	OPTIONAL { ?b con:office ?office3 . ?office3 con:address ?address3 . ?address3 con:street ?street_address }
.	OPTIONAL { ?b con:office ?office4 . ?office4 con:address ?address4 . ?address4 con:street2 ?extended_address }
.	OPTIONAL { ?b con:office ?office5 . ?office5 con:phone ?phone }
.	OPTIONAL { ?b con:office ?office6 . ?office6 geo:lat ?lat }
.	OPTIONAL { ?b con:office ?office7 . ?office7 geo:long ?lng }
}"""

			for row in graph.query(query_foaf, initNs = self.initNs):
				rd = self._Valued(graph, row, [ 
					"uri", 
					"name", "nick", "img", "image", "weblog", "page", "profile", "homepage", "mbox_sha1sum", 
					"locality", "country_name", "postal_code", "street_address", "extended_address",
					"phone",
					"lat", "lng",
				])
				yield	self._ProcessRow(rd, uri = rd.pop("uri"), rel = "contact")

		except:
			Log(exception = True)

	def _ProcessRow(self, rd, uri, rel = None):
		d = {}

		#
		#	Title
		#
		d['title'] = rd['title'] = rd.get('name') or rd.get('nick') or '[No Name]'

		#
		#	Image
		#
		logo = rd.get('image') or rd.get('img')
		if logo:
			rd['logo'] = logo
			d['logo'] = logo

		#
		#	Lat/Lng
		#
		bm_api.add_latlon(d, rd.get('lat'), rd.get('lng'))

		#
		#	Get everything that goes into the hCard
		#
		hd = uf_mfdict.mfdict()
		for k_from, k_to in [
			( "country_name", "%s.%s" % ( uf_vcard.ADR, uf_vcard.CountryName, ), ),
			( "street_address", "%s.%s" % ( uf_vcard.ADR, uf_vcard.StreetAddress, ), ),
			( "extended_address", "%s.%s" % ( uf_vcard.ADR, uf_vcard.ExtendedAddress, ), ),
			( "locality", "%s.%s" % ( uf_vcard.ADR, uf_vcard.Locality, ), ),
			( "region", "%s.%s" % ( uf_vcard.ADR, uf_vcard.Region, ), ),
			( "postal_code", "%s.%s" % ( uf_vcard.ADR, uf_vcard.PostalCode, ), ),
			( "title", uf_vcard.FN, ),
			( "mbox_sha1sum", uf_vcard.UID, ),
			( "phone", "%s.%s" % ( uf_vcard.TEL, uf_vcard.Voice, ), ),
			( "logo", uf_vcard.Logo, ),
			( "lat", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Latitude, ), ),
			( "lng", "%s.%s" % ( uf_vcard.GEO, uf_vcard.Longitude, ), ),
		]:
			try:
				value = bm_extract.as_string(rd, k_from)
				if value:
					if k_from in [ "phone" ]:
						if value.startswith("tel:"):
							value = value[4:]

					hd[k_to] = value

				rd.pop(k_from)
			except KeyError:
				pass

		for key in [ "name", "nick", "photo", "image", "img", ]:
			try: rd.pop(key)
			except KeyError: pass

		if hd:
			uf_vcard.scrub(hd)
			d["hcard:hcard"] = hcard.decompose(hd, "hcard")

		#
		#	Add links
		#
		d["link"] = rd.get('homepage') or rd.get("weblog") or uri

		links = [{
			"rel" : "related",
			"href" : uri,
			"title" : "FOAF source",
		}]
		d["links"] = links

		for html_key in [ "homepage", "weblog", ]:
			try:
				uri = rd.pop(html_key)
				if uri:
					links.append({
						"href" : uri,
						"rel" : "related",
						"type" : "text/html",
						"title" : html_key,
					})
			except KeyError:
				pass

		if uri != self.uri and rel:
			links.append({
				"href" : self.uri,
				"rel" : "xfn",
				"rev" : rel
			})

##		if rel:
##			d["xfn:rel"] = rel

		return	d

	def _Dump(self, graph):
		print graph.serialize(format = "n3")
		for row in graph: print row

	def _Value(self, graph, node, key):
		if node == None:
			return	None

		if node.__class__ == rdflib.BNode:
			for triple in graph.triples(( node, rdflib.URIRef('resource'), None)):
				if triple[2].__class__ == rdflib.Literal:
					return	str(triple[2])

		return	str(node)

	def _Valued(self, graph, row, names):
		d = {}

		count = -1
		for name in names:
			count += 1
			d[name] = self._Value(graph, row[count], name)

		return	d

if __name__ == '__main__':
	uri = 'http://www.w3.org/People/Berners-Lee/card'

	api = FOAF(uri = uri)
	for item in api.items:
		Log(item = item)
