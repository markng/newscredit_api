#
#   api_calais.py
#
#   David Janes
#   2009.01.19
#
#	Copyright 2009 David Janes
#
#	Reuters Calaias API
#

import os
import sys
import urllib
import types
import pprint
import types
import StringIO

import bm_extract
import bm_uri
import bm_api
import bm_cfg
import bm_work

from bm_log import Log

try:
	import json
except ImportError:
	import simplejson as json

class Calais(bm_api.APIReader):
	"""API to mark up data with information from Calais"""

	relevance = 0.2;							## minimum relevance
	tag = True									## add Calaias tags to categories
	wikipedia = True							## add Wikipedia links to posts
	geotag = True								## geotag the item with the best geo match
	microformats = True							## add microformats to a document ... not implemented yet
	types = [ 
		"Person", 
		"City", 
		"Country", 
		"ProvinceOrState",
		"Company",
	]											## types of results we are interested in

	_api_key = None
	_calais = None

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def GetMeta(self):
		"""No metadata (yet?)"""

		return	{}

	def IterItems(self):
		"""See bm_api.IterItems
		
		self._request_items is called upon api.items = [ ... ]
		"""

		assert(self._calais), "programming error - Restart should have been called first"""

		for itemd in self._request_items or []:
			#
			#	A little convoluted, needed for rewriting at the end
			#
			summary = None
			content = bm_extract.as_string(itemd, "content")
			if not content:
				summary = bm_extract.as_string(itemd, "summary")

			body = content or summary
			if not body:
				yield itemd
				continue

			#
			#	Process, narrow, and sort by most relevant first
			#
			entities = self._calais.analyze(body, content_type = "TEXT/HTML").entities
			if self.types:
				entities = filter(lambda e: e["_type"] in self.types, entities)
			entities = filter(lambda e: e["relevance"] >= self.relevance, entities)
			entities.sort(lambda a, b: cmp(a["relevance"], b["relevance"]))
			entities.reverse()

			if not entities:
				yield itemd
				continue

			#
			#	Add categories from results
			#
			if self.tag:
				categorys = bm_extract.as_list(itemd, "category")

				for entity in entities:
					categorys.append({ "term" : entity["name"] })

				itemd["category"] = categorys


			#
			#	Geotag
			#
			if self.geotag:
				for entity in entities:
					lat = bm_extract.as_string(entity, 'resolutions.latitude')
					lon = bm_extract.as_string(entity, 'resolutions.longitude')

					bm_api.add_latlon(itemd, lat, lon)

			rewrites = []

			#
			#	Wikipedia ... rewrite 
			#
			if self.wikipedia:
				for entity in entities:
					name = bm_extract.as_string(entity, 'name')
					length = bm_extract.as_int(entity, 'instances.length')
					offset = bm_extract.as_int(entity, 'instances.offset')

					offset = body.find(name, offset)
					if offset == -1:
						Log("MISSED", name = name, entities = entities)
						continue

					name = name.replace(' ', '_')
					name = urllib.quote(name, safe = '_.-')

					rewrites.append(( 
						offset, 
						0, 
						'<a href="http://en.wikipedia.org/wiki/%s" class="calais calais-%s"><img src="%s" border="0" /></a>' % (
							name, 
							entity["_type"],
							"http://www.opencalais.com/files/wpro_shared/images/Calais%20icon_16x16.jpg",
						)
					))

			#
			#	Rewrite the document?
			#
			if rewrites:
				rewrites.sort()
				rewrites.reverse()

				for offset, length, text in rewrites:
					body = body[:offset] + text + body[offset + length:]

				if content:
					itemd["content"] = body
				else:
					itemd["summary"] = body

			yield	itemd

	def Restart(self):
		bm_api.APIReader.Restart(self)

		if not self._calais:
			api_key = self._api_key or bm_cfg.cfg.as_string('calais.api_key')
			if not api_key:
				raise	KeyError, "_api_key required to use Calais"

			self._calais = CalaisAPI(api_key, submitter = "Pipe Cleaner")

#
#	Below here, this is all from:
#	python-calais v.1.4 -- Python interface to the OpenCalais API
#	Author: Jordan Dimov (jdimov@mlke.net)
#	Last-Update: 01/12/2009
#	
#
PARAMS_XML = """
<c:params xmlns:c="http://s.opencalais.com/1/pred/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> <c:processingDirectives %s> </c:processingDirectives> <c:userDirectives %s> </c:userDirectives> <c:externalMetadata %s> </c:externalMetadata> </c:params>
"""

class CalaisAPI:
	"""
	Python class that knows how to talk to the OpenCalais API.  Use the analyze() and analyze_url() methods, which return CalaisResponse objects.  
	"""
	api_key = None
	processing_directives = {"contentType":"TEXT/RAW", "outputFormat":"application/json", "reltagBaseURL":None, "calculateRelevanceScore":"true", "enableMetadataType":None, "discardMetadata":None, "omitOutputtingOriginalText":"true"}
	user_directives = {"allowDistribution":"false", "allowSearch":"false", "externalID":None}
	external_metadata = {}

	def __init__(self, api_key, submitter="python-calais client v.%s" % "0"):
		self.api_key = api_key
		self.user_directives["submitter"]=submitter

	def _get_params_XML(self):
		return PARAMS_XML % (" ".join('c:%s="%s"' % (k,v) for (k,v) in self.processing_directives.items() if v), " ".join('c:%s="%s"' % (k,v) for (k,v) in self.user_directives.items() if v), " ".join('c:%s="%s"' % (k,v) for (k,v) in self.external_metadata.items() if v))

	def rest_POST(self, content):
		loader = bm_uri.URILoader(
			uri = "http://api.opencalais.com/enlighten/rest/", 
			data = {
				'licenseID' : self.api_key, 
				'content' : content,
				'paramsXML' : self._get_params_XML(),
			},
			method = "POST",
			cachable = True,
			min_retry = 3600 * 24 * 28,	## cache Calais results for 28 days
		)
		return	loader.Load()

	def analyze(self, content, content_type="TEXT/RAW", external_id=None):
		self.processing_directives["contentType"]=content_type.upper()
		if external_id:
			self.user_directives["externalID"] = external_id
		return CalaisResponse(self.rest_POST(content or ""))

class CalaisResponse():
	"""
	Encapsulates a parsed Calais response and provides easy pythonic access to the data.
	"""
	raw_response = None
	simplified_response = None
	
	def __init__(self, raw_result):
		self.entities = []
		try:
			self.raw_response = json.load(StringIO.StringIO(raw_result))
		except:
			raise ValueError(raw_result)
		self.simplified_response = self._simplify_json(self.raw_response)
		self.__dict__['doc'] = self.raw_response['doc']
		for k,v in self.simplified_response.items():
			self.__dict__[k] = v

	def _simplify_json(self, json):
		result = {}
		# First, resolve references
		for element in json.values():
			for k,v in element.items():
				if isinstance(v, unicode) and v.startswith("http://") and json.has_key(v):
					element[k] = json[v]
		for k, v in json.items():
			if v.has_key("_typeGroup"):
				group = v["_typeGroup"]
				if not result.has_key(group):
					result[group]=[]
				del v["_typeGroup"]
				v["__reference"] = k
				result[group].append(v)
		return result


if __name__ == '__main__':
	import bm_io

	bm_cfg.cfg.initialize()

	items = [
		{
			"title" : "Song of the Week #113 by Jerome Kern and Otto Harbach",
			"content" : bm_io.readfile("data/calais.1.txt"),
		}
	]

	api = Calais(geotag = True, wikipedia = True)
	api.items = items
	for item in api.items:
		## pprint.pprint(item)
		print item["content"]
