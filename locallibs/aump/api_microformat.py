#
#   api_microformat.py
#
#   David Janes
#   2008.12.28
#
#	Copyright 2008 David Janes
#

import os
import os
import sys
import urllib
import types
import pprint
import types

import bm_extract
import bm_uri
import bm_api

from bm_log import Log

import hatom
import hcalendar
import hcard
import hdocument

class Microformat(bm_api.APIBase):
	_parser = None
	_meta = {}
	_items = []
	_required_properties = [ "uri", ]

	def __init__(self, **ad):
		bm_api.APIBase.__init__(self, **ad)

	def GetMeta(self):
		self.Fetch()

		return	self._meta

	def IterItems(self):
		self.Fetch()

		for item in self._items:
			if self.AtomLike():
				yield	self.CustomizeAtomItem(item)
			else:
				yield	item

	def Fetch(self):
		raise	NotImplementedError

	def CustomizeReset(self):
		self._parser = None

	def ExtractCategories(self, itemd):
		try:
			tags = itemd.pop("tag")
			if tags:
				cats = []
				for tagd in tags:
					cats.append({
						"term" : tagd["@@title"],
					})

				itemd["category"] = cats
		except KeyError:
			pass

class SimpleMicroformat(Microformat):
	_parser_class = None
	_parserd = {}

	def __init__(self, **ad):
		Microformat.__init__(self, **ad)

	def Fetch(self):
		if self._parser:
			return

		self.CustomizeValidate()

		self._parser = self._parser_class(page_uri = self.uri, at_prefix = '@@', **self._parserd)
		self._parser.PragmaCLI()
		self._items = list(self._parser.Iterate())
		self._meta = {
			"link" : self.uri,
			"title" : self._parser.document_title,
		}

		if self._parser.document_date:
			self._meta['updated'] = bm_extract.coerce_datetime(self._parser.document_date).isoformat()

class HAtom(SimpleMicroformat):
	_parser_class = hatom.MicroformatHAtom
	_atom_item = {
		"content" : "entry-content",
		"summary" : "entry-summary",
		"title" : "entry-title",
		"link" : "bookmark",
		"published" : "published",
	}

	def CustomizeAtomItem(self, itemd):
		try:
			author = itemd.pop("author")
			if author:
				itemd["author"] = bm_extract.as_string(author, "@@title")

				if bm_extract.is_list(author) or bm_extract.is_list_like(author):
					itemd["hcard:author"] = map(lambda a: hcard.decompose(a, "hcard"), author)
				elif bm_extract.is_dict(author):
					itemd["hcard:author"] = hcard.decompose(author, "hcard")
		except KeyError:
			pass

		self.ExtractCategories(itemd)

		return	bm_api.APIBase.CustomizeAtomItem(self, itemd)

class HCalendar(SimpleMicroformat):
	_parser_class = hcalendar.MicroformatHCalendar

	def CustomizeAtomItem(self, itemd):
		return	{
			"title" : bm_extract.as_string(itemd, "@@title"),
			"content" : bm_extract.as_string(itemd, "@@html"),
			"link" : itemd.find('url') or bm_extract.as_string(itemd, "@@uri"),
			"hcalendar:hcalendar" : hcalendar.decompose(itemd, "hcalendar"),
		}

class HCard(SimpleMicroformat):
	_parser_class = hcard.MicroformatHCard

	def CustomizeAtomItem(self, itemd):
		return	{
			"title" : bm_extract.as_string(itemd, "@@title"),
			"content" : bm_extract.as_string(itemd, "@@html"),
			"link" : itemd.find('url') or bm_extract.as_string(itemd, "@@uri"),
			"hcard:hcard" : hcard.decompose(itemd, "hcard"),
		}

class Document(Microformat):
	field = "a"

	_properties = [ "uri", "field" ]
	_required_properties = [ "uri", "field" ]

	def __init__(self, **ad):
		Microformat.__init__(self, **ad)

	def Fetch(self):
		if self._parser:
			return

		self.CustomizeValidate()

		self._parser = hdocument.MicroformatDocument(page_uri = self.uri, at_prefix = '@@')
		self._parser.PragmaCLI()

		for resultd in self._parser.Iterate():
			self._items = resultd.get(self.field) or []
			break

class Feeds(SimpleMicroformat):
	_parser_class = hdocument.MicroformatDocument

	def IterItems(self):
		self.Fetch()

		yield {
			"link" : self.uri,
			"title" : self._parser.document_title,
			"feeds" : [ item["src"] for item in self._items[0]["feed"] ],
		}

if __name__ == '__main__':
	to_test = 'hcard'

	if to_test == 'hatom':
		api = HAtom(_atom_like = True)
		api.request = {
			"uri" : "http://tantek.com/",
		}

		count = -1
		for item in api.items:
			count += 1
			pprint.pprint(item)
			## Log(count = count, item = item)
			break

		pprint.pprint(api.meta)

	if to_test == 'hcalendar':
		api = HCalendar()
		api.request = {
			"uri" : "http://tantek.com/",
		}

		count = -1
		for item in api.items:
			count += 1

			pprint.pprint(item, width = 1)

	if to_test == 'hcard':
		api = HCard()
		api.request = {
			"uri" : "http://tantek.com/",
		}

		count = -1
		for item in api.items:
			count += 1

			pprint.pprint(item, width = 1)

	if to_test == 'feeds':
		api = Feeds()
		api.request = {
			"uri" : "http://code.davidjanes.com/blog/"
		}

		count = -1
		for item in api.items:
			count += 1

			pprint.pprint(item, width = 1)

	if to_test == 'document':
		api = Document()
		api.request = {
			"uri" : "http://twitter.com/dpjanes",
			"field" : "image",
		}

		count = -1
		for item in api.items:
			count += 1

			pprint.pprint(item, width = 1)

		api.request = {
			"uri" : "http://twitter.com/dpjanes",
			"field" : "a",
		}

		count = -1
		for item in api.items:
			count += 1

			pprint.pprint(item, width = 1)
