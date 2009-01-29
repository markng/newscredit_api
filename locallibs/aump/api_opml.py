#
#   api_opml.py
#
#   David Janes
#   2009.01.17
#
#	Copyright 2009 David Janes
#
#	OPML Parser and writer
#
#

import os
import os
import sys
import urllib
import types
import pprint
import types
import time
import datetime

try:
	import json
except:
	import simplejson as json

import bm_extract
import bm_uri
import bm_api
import bm_work

from bm_log import Log

class OPML(bm_api.APIReader):
	_item_path = "body.outline"
	_meta_path = "head"
	_uri_param = True
	_convert2work = bm_work.XML2WORK(keep_attributes = True, attribute_prefix = '')

	#
	#	If True, outlines are returned one in a row
	#
	_flat = True
	
	#
	#	If True, we only return leaf nodes
	#
	_leaf_only = False

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def IterItems(self):
		for itemd in bm_api.APIReader.IterItems(self):
			if self._flat:
				for subitem in self.Flatten(itemd):
					yield self.ScrubItem(subitem)
			else:
				yield self.ScrubItem(itemd)

	def CustomizeAtomMeta(self, itemd):
		itemd = dict(itemd)

		#
		#	datetimes
		#
		for k_to, k_from in [ ( 'created', 'dateCreated' ), ( 'updated', 'dateModified' ), ]:
			try:
				value = itemd.pop(k_from)
				itemd[k_to] = bm_extract.coerce_datetime(value, otherwise = value, atom = True)
			except KeyError:
				pass

		#
		#	OPML Garbage
		#
		for key in [ 'expansionState', 'vertScrollState', 'windowBottom', 'windowLeft', 'windowRight', 'windowTop', ]:
			try: del itemd[key]
			except: pass

		#
		#	Atom author
		#
		try: author_name = itemd.pop("ownerName")
		except: author_name = None

		try: author_email = itemd.pop("ownerEmail")
		except: author_email = None

		try: author_href = itemd.pop("ownerId")
		except: author_href = None

		if author_name or author_email or author_href:
			authord = {
				"@" : author_name or "",
			}
			if author_email: authord["email"] = author_email
			if author_href: authord["uri"] = author_href

			itemd["author"] = authord

		return	itemd

	def ScrubItem(self, itemd):
		"""Note: *not* CustomizeAtomItem"""

		if not self.AtomLike():
			return	itemd

		itemd = dict(itemd)

		#
		#	Atom title
		#
		try:
			if not itemd.get("title"):
				itemd["title"] = itemd.pop("text")
		except KeyError:
			pass

		#
		#	Atom datetimes
		#
		try:
			created = itemd.pop("created")
			itemd["created"] = bm_extract.coerce_datetime(created, otherwise = created, atom = True)
		except KeyError:
			pass

		#
		#	Atom categories
		#
		try:
			tags = itemd.pop("tags")
			tags = bm_extract.coerce_list(tags, separator = ",", strip = True)

			itemd["category"] = [ { "term" : tag } for tag in tags ]
		except KeyError:
			pass

		return	itemd

	def Flatten(self, item, path = None):
		path = path or []

		children = bm_extract.as_list(item, "outline")

		#
		#
		#
		nitem = dict()

		for key, value in item.iteritems():
			if key != "outline":
				nitem[key] = value

		item = nitem
		if path:
			item["tags"] = bm_extract.coerce_string(path, separator = ", ")

		item["@@children"] = len(children)

		#
		#
		#
		if not self._leaf_only or len(children) == 0:
			yield item

		#
		#
		#
		for child in children:
			for child_item in self.Flatten(child, list(path) + [ item.get("text", "") ]):
				yield	child_item

class OPMLWriter(bm_api.XMLAPIWriter):
	namespaced = bm_api.namespaced

	def CustomizeProduce(self):
		e_opml = self.MakeElement("opml")
		e_opml.set("version", "2.0")
		e_opml.set("encoding", "utf-8")

		e_head = self.MakeElement("head", parent = e_opml)
		self.TranscribeNode(e_head, self.ScrubMeta(self.GetMeta()))

		e_body = self.MakeElement("body", parent = e_opml)
		for itemd in self.IterItems():
			e_item = self.MakeElement("outline", parent = e_body)
			self.TranscribeNode(e_item, self.ScrubEntry(itemd))

	def FirstInListLikeObject(self, value, otherwise = None):
		if bm_extract.is_list(value):
			if value:
				return	value[0]

			return	None

		if bm_extract.is_list_like(value):
			any = False
			for sub in value:
				return	value

			return	None

		return	otherwise

	def ScrubMeta(self, itemd):
		itemd = dict(itemd)
		itemd.setdefault("title", "[Untitled]")

		if self.AtomLike():
			#
			#	Author is close enough to owner
			#
			author_name = bm_extract.as_string(itemd, "author")
			if author_name:
				itemd["ownerName"] = author_name
			
			author_href = bm_extract.as_string(itemd, "author.uri")
			if author_href:
				itemd["ownerId"] = author_href
			
			author_email = bm_extract.as_string(itemd, "author.email")
			if author_email:
				itemd["ownerEmail"] = author_email

			try: itemd.pop("author")
			except KeyError: pass

			#
			#
			#
			for k_from, k_to in [ ( 'created', 'dateCreated' ), ( 'updated', 'dateModified' ), ]:
				try:
					value = itemd.pop(k_from)
					itemd[k_to] = bm_extract.coerce_datetime(value, otherwise = value, rfc822 = True)
				except KeyError:
					pass

		return	itemd

	def ScrubEntry(self, itemd):
		if bm_extract.is_dict(itemd):
			nd = {}

			seen_html = False
			seen_rss = False
			seen_url = False

			for key, value in itemd.iteritems():
				if self.AtomLike():
					if key == "link":
						key = "htmlUrl"
					elif key == "feeds":
						key = "rssUrl"
					elif key == "content":
						key = "description"
					elif key == "title":
						key = "text"
					elif key == "category":
						key = "tags"
						value = ", ".join(map(lambda d: d["term"], value))
					elif key == "links":
						for ld in bm_extract.coerce_list(value):
							if bm_extract.as_string(ld, "rel") == "alternate":
								key = "rssUrl"
								value = bm_extract.as_string(ld, "href")

					#
					#	datetimes (?)
					#
					try:
						created = itemd.pop("created")
						itemd["created"] = bm_extract.coerce_datetime(created, otherwise = created, rfc822 = True)
					except KeyError:
						pass


				if key == "rssUrl":
					value = self.FirstInListLikeObject(value, value)
					if value == None:
						continue

					seen_rss = True
				elif key == "htmlUrl":
					value = self.FirstInListLikeObject(value, value)
					if value == None:
						continue

					seen_html = True
				elif key == "url":
					seen_url = True

				if key in [ "items", "outline" ]:
					nd["outline"] = self.ScrubEntry(value)
				elif value == None:
					pass
				elif bm_extract.is_atomic(value):
					nd['@%s' % key] = value

			if seen_rss:
				nd.setdefault("@type", "rss")
			elif seen_html:
				nd.setdefault("@type", "link")
			elif seen_url:
				nd.setdefault("@type", "link")

			nd.setdefault("@text", "")

			return	nd
		elif bm_extract.is_atomic(itemd):
			return	{
				"@title" : bm_extract.coerce_string(itemd)
			}
		elif bm_extract.is_list(itemd) or bm_extract.is_list_like(itemd):
			return	map(self.ScrubEntry, itemd)
			
		return	itemd

if __name__ == '__main__':
	import xml.etree.ElementTree as ElementTree

	if True:
		writer = OPMLWriter()
		writer.items = [
			{
				"title" : "Post #1",
				"description" : "This is the data",
				"items" : [
					"A", "B", "C"
				],
				"link" : "http://www.davidjanes.com",
				"feeds" : "http://www.davidjanes.com/blog/feed",
			},
		]
		writer.request = {
			"title" : "My Document",
			"author" : {
				"@" : "David Janes",
				"email" : "example@example.com",
				"uri" : "http://code.davidjanes.com",
			}
		}

		print writer.Produce()

	if False:
		import api_feeds

		api = api_feeds.Feeds()
		api.request = {
			"uri" : "http://feeds.feedburner.com/DavidJanesCode",
		}

		writer = OPMLWriter()
		writer.items = api.items

		print writer.Produce()

	if False:
		Log.verbose = True
		api = OPML(uri = 'http://hosting.opml.org/dave/spec/states.opml')
		for index, item in enumerate(api.items):
			## pprint.pprint(( index, item ))
			pprint.pprint(item)

		pprint.pprint(api.meta)

