#
#   api_html.py
#
#   David Janes
#   2009.01.14
#
#	Copyright 2008 David Janes
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
import bm_work

from bm_log import Log

class Downloaders(bm_api.APIReader):
	@apply
	def item_path():
		def fset(self, path):
			self._item_path = path

		return property(**locals())

class HTML(Downloaders):
	_convert2work = bm_work.HTML2WORK(keep_attributes = True)
	_item_path = "body"

	def __init__(self, **ad):
		Downloaders.__init__(self, **ad)

	def CustomizeDownloadPage(self):
		"""See bm_api.APIReader.CustomizeDownloadPage"""

		try:
			loader = bm_uri.HTMLLoader(
				self.ConstructPageURI(), 
				referer = self._http_referer,
				user_agent = self._http_user_agent,
				**self._http_ad
			)
			loader.Load()
		except bm_uri.NotModified:
			pass
		except bm_uri.DownloaderError:
			return	None

		return	self._convert2work.FeedString(loader.GetCooked())

class JSON(Downloaders):
	_convert2work = bm_work.JSON2WORK()
	_item_path = ""

	def __init__(self, **ad):
		Downloaders.__init__(self, **ad)

class XML(Downloaders):
	"""Download an XML document, only using the text between tags as data"""

	_convert2work = bm_work.XML2WORK(keep_attributes = False)
	_item_path = ""

	def __init__(self, **ad):
		Downloaders.__init__(self, **ad)

class XMLAttributes(Downloaders):
	"""Download an XML document, preserving attributes (as '@' attributes)"""

	_convert2work = bm_work.XML2WORK(keep_attributes = True)
	_item_path = ""

	def __init__(self, **ad):
		Downloaders.__init__(self, **ad)

class XMLAttributesAsText(Downloaders):
	"""Download an XML document, treating attributes as nodes"""

	_convert2work = bm_work.XML2WORK(keep_attributes = True, attribute_prefix = '')
	_item_path = ""

	def __init__(self, **ad):
		Downloaders.__init__(self, **ad)

if __name__ == '__main__':
	Log.verbose = True

	to_test = "json_path"

	if to_test == "html":
		api = HTML(
			uri = "http://www.toronto.ca/fire/cadinfo/livecad.htm", 
			item_path = "body.table[2].tr.td[2].table.tr[4].td.table.tr",
		)
		for item in api.items:
			pprint.pprint(item)
	elif to_test == "json_list":
		api = JSON(
			uri = "http://labs.adobe.com/technologies/spry/data/json/array-03.js",
		)
		for item in api.items:
			pprint.pprint(item)
		pprint.pprint(api.response)
	elif to_test == "json_path":
		api = JSON(
			uri = "http://www.google.com/calendar/feeds/c4o4i7m2lbamc4k26sc2vokh5g%40group.calendar.google.com/public/full?alt=json-in-script",
			item_path = "feed.entry",
		)
		for item in api.items:
			pprint.pprint(item)


