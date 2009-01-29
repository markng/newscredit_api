#
#   api_feed.py
#
#   David Janes
#   2008.12.23
#
#	Copyright 2008 David Janes
#
#	RSS and other feeds
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

from bm_log import Log

class Feed(bm_api.APIReader):
	_item_path = "entries"
	_meta_path = "feed"
	_uri_param = True
	_scrub = True

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def CustomizeDownloadPage(self):
		"""See bm_api.APIReader.CustomizeDownloadPage"""

		import bm_feedparser

		uri = self.ConstructPageURI()

		loader = bm_uri.URILoader(
			uri = uri,
			referer = self._http_referer,
			user_agent = self._http_user_agent,
			**self._http_ad
		)

		d = bm_feedparser.parse(uri, loader = loader)
		if self._scrub:
			self.Scrub(d["feed"])
			for entry in d["entries"]:
				self.Scrub(entry)

		return	d

	def Scrub(self, item):
		for key in [ "updated", "created", "published", "expired", ]:
			parsed = item.get("%s_parsed" % key)
			if not parsed or not hasattr(parsed, "__len__") or len(parsed) != 9:
				continue

			value = time.strftime("%Y-%m-%dT%H:%M:%S%z", parsed)
			if value.endswith("+0000"):
				value = value[:-2] + ":00"

			item[key] = value
			
		for key, value in list(item.iteritems()):
			if key.endswith("_detail") or key.endswith("_parsed"):
				try: del item[key]
				except: pass

		if item.get('tags'):
			tags = []

			for tagd in item['tags']:
				if type(tagd) in types.StringTypes:
					tags.append(tagd)
				elif isinstance(tagd, dict) and tagd.get('term'):
					tags.append(tagd['term'])

			item["tags"] = tags

class RSS20(bm_api.APIReader):
	"""Prefer to use the class 'Feed', above"""

	_item_path = "channel.item"
	_meta_path = "channel"
	_meta_removes = [ "item", ]
	_uri_param = True

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

class RSS20Writer(bm_api.XMLAPIWriter):
	namespaced = bm_api.namespaced

	_known_channel = [
		"category",
		"cloud",
		"copyright",
		"description",
		"docs",
		"generator",
		"image",
		"language",
		"lastBuildDate",
		"link",
		"managingEditor",
		"pubDate",
		"rating",
		"skipDays",
		"skipHours",
		"textInput",
		"title",
		"ttl",
		"webMaster",
	]

	_known_item = [
		"title",
		"link",
		"description",
		"category",
		"comments",
		"enclosure",
		"guid",
		"pubDate",
		"source",
		"comments",
	]

	def CustomizeProduce(self):
		e_rss = self.MakeElement("rss")
		e_rss.set("version", "2.0")

		e_channel = self.MakeElement("channel", parent = e_rss)
		self.TranscribeNode(e_channel, self.ScrubMeta(self.GetMeta()))

		for itemd in self.IterItems():
			e_item = self.MakeElement("item", parent = e_channel)
			self.TranscribeNode(e_item, self.ScrubEntry(itemd))

	def ScrubMeta(self, itemd):
		"""Make sure we look like an RSS feed"""

		#
		#	Look for known items and namespaced items
		#
		nd, xd = self.Separate(itemd, self._known_channel, "rss")

		#
		#	atom links
		#	{'links': [{'href': u'http://code.davidjanes.com/blog',
		#				'rel': 'alternate',
		#				'type': 'text/html'},
		#			   {'href': u'http://feeds.feedburner.com/DavidJanesCode',
		#				'rel': u'self',
		#				'type': u'application/rss+xml'}],
		#
		try:
			links = xd.pop('links')
			if links:
				nd["atom:links"] = links

				#
				#	default an RSS value
				#
				if not nd.get("link"):
					ld = dict([ ( l["rel"], l ) for l in links ])
					v = ld.get("alternate") or ld.get("self")
					if v:
						nd["link"] = v["href"]
		except KeyError:
			pass

		#
		#	atom updated
		#	 'updated': '2009-01-09T12:20:02+00:00'}
		#
		try:
			value = xd.pop('updated')
			if value:
				nd["atom:updated"] = value
		except KeyError:
			pass

		#
		#	atom published/updated
		#	 'updated': '2009-01-09T12:20:02+00:00'}
		#
		for key in [ 'updated', 'published' ]:
			#
			#	atom updated / published
			#	 'updated': '2009-01-09T12:20:02+00:00'}
			#
			try:
				value = xd.pop('%s' % key)
				if value:
					nd["atom:%s" % key] = value
			except KeyError:
				pass

		#
		#	author
		#
		try:
			value = xd.pop('author')
			if value:
				nd["managingEditor"] = value
				nd["atom:author"] = value
				nd["dc:creator"] = value
		except KeyError:
			pass

		#
		#	default a pubDate
		#
		if not nd.get("pubDate"):
			dts = nd.get("atom:updated") or nd.get("atom:published")
			if dts:
				try:
					import dateutil.parser

					dt = dateutil.parser.parse(dts)
					if dt:
						nd["pubDate"] = dt.strftime("%a, %d %b %Y %H:%M:%S %z");
				except:
					Log("date could not be parsed - maybe a missing module?", exception = True, dts = dts)
					
		#
		#	atom subtitle
		#
		try:
			value = xd.pop('subtitle')
			if value:
				nd["atom:subtitle"] = value

				if not nd.get("title"):
					nd["title"] = value

				if not nd.get("description"):
					nd["description"] = value
		except KeyError:
			pass

		#
		#	Required channel elements
		#
		nd.setdefault("title", "");
		nd.setdefault("link", "#");
		nd.setdefault("description", "");

		#
		#	Remaining items
		#
		if xd:
			for key, item in xd.iteritems():
				nd["unknown:%s" % key] = item

		return	nd

	def ScrubEntry(self, itemd):
		"""Make sure we look like an RSS entry"""

		#
		#	Look for known items and namespaced items
		#
		nd, xd = self.Separate(itemd, self._known_item, "rss")

		#
		#	atom links
		#
		try:
			links = xd.pop('links')
			if links:
				nd["atom:links"] = links

				#
				#	default an RSS value
				#
				if not nd.get("link"):
					ld = dict([ ( l["rel"], l ) for l in links ])
					v = ld.get("alternate") or ld.get("self")
					if v:
						nd["link"] = v["href"]
		except KeyError:
			pass

		#
		#	author.uri
		#
		try:
			value = bm_extract.as_string(xd, 'author.uri')
			if value:
				nd["source"] = value
		except KeyError:
			pass
			
		#
		#	author
		#
		try:
			value = xd.pop('author')
			if value:
				value = bm_extract.coerce_string(value)
			if value:
				nd["atom:author"] = value
				nd["dc:creator"] = value
		except KeyError:
			pass

		#
		#	atom published/updated
		#	 'updated': '2009-01-09T12:20:02+00:00'}
		#
		for key in [ 'updated', 'published' ]:
			#
			#	atom updated / published
			#	 'updated': '2009-01-09T12:20:02+00:00'}
			#
			try:
				value = xd.pop('%s' % key)
				if value:
					nd["atom:%s" % key] = value
			except KeyError:
				pass

		#
		#	default a pubDate
		#
		if not nd.get("pubDate"):
			dts = nd.get("atom:updated") or nd.get("atom:published")
			if dts:
				try:
					import dateutil.parser

					dt = dateutil.parser.parse(dts)
					if dt:
						nd["pubDate"] = dt.strftime("%a, %d %b %Y %H:%M:%S %z")
				except:
					Log("date could not be parsed - maybe a missing module?", exception = True, dts = dts)

		#
		#	Our fake composite value, body
		#
		try:
			value = xd.pop("body")
			if value:
				nd["description"] = value
		except KeyError:
			pass

		#
		#	Atom content
		#
		try:
			value = xd.pop("content")
			if value:
				nd.setdefault("description", value)
				nd["atom:content"] = value
		except KeyError:
			pass

		#
		#	Atom summary
		#
		try:
			value = xd.pop("summary")
			if value:
				nd.setdefault("description", value)
				nd["atom:summary"] = value
		except KeyError:
			pass

		#
		#	Atom ID
		#
		try:
			value = xd.pop("id")
			if value:
				nd.setdefault("guid", value)
				nd["atom:id"] = value
		except KeyError:
			pass

		#
		#	Required item elements
		#
		nd.setdefault("title", "");
		nd.setdefault("link", "#");
		nd.setdefault("description", "");

		#
		#	Remaining items
		#
		if xd:
			for key, item in xd.iteritems():
				nd["unknown:%s" % key] =  item

		return	nd

class AtomWriter(bm_api.XMLAPIWriter):
	namespaced = bm_api.namespaced

	_known_feed = [
		"id",
		"title",
		"updated",

		"category",
		"author",
		"contributor",
		"generator",
		"icon",
		"logo",
		"rights",
		"subtitle",

		"link",
		"links",
	]

	_known_entry = [
		"id",
		"title",
		"updated",

		"author",
		"content",
		"summary",

		"category",
		"contributor",
		"published",
		"source",
		"rights",

		"link",
		"links",
	]

	def CustomizeProduce(self):
		e_feed = self.MakeElement("feed")

		self.TranscribeNode(e_feed, self.ScrubMeta(self.GetMeta()))

		for itemd in self.IterItems():
			e_item = self.MakeElement("item", parent = e_feed)
			self.TranscribeNode(e_item, self.ScrubEntry(itemd))

	def ScrubMeta(self, itemd):
		"""Make sure we look like an Atom feed"""

		#
		#	Look for known items and namespaced items
		#
		nd, xd = self.Separate(itemd, self._known_feed, "atom")

		#
		#	Fix up to look Atomish
		#
		self.ScrubPerson(nd, "contributor")
		self.ScrubPerson(nd, "author")
		self.ScrubCategory(nd)
		self.ScrubLinks(nd)

		#
		#	Required feed elements
		#
		nd.setdefault("title", "");
		nd.setdefault("link", "#");

		#
		#	Remaining unknown items
		#
		for key, item in xd.iteritems():
			nd["unknown:%s" % key] =  item

		return	nd

	def ScrubEntry(self, itemd):
		"""Make sure we look like an Atom entry"""

		#
		#	Look for known items and namespaced items
		#
		nd, xd = self.Separate(itemd, self._known_entry, "atom")

		#
		#	Fix up to look Atomish
		#
		self.ScrubPerson(nd, "contributor")
		self.ScrubPerson(nd, "author")
		self.ScrubCategory(nd)
		self.ScrubLinks(nd)

		#
		#	Required item elements
		#
		nd.setdefault("title", "");
		nd.setdefault("link", "#");

		#
		#	Remaining unknown items
		#
		for key, item in xd.iteritems():
			nd["unknown:%s" % key] =  item

		return	nd

	def ScrubPerson(self, itemd, person_key):
		persons = bm_extract.as_list(itemd, person_key)
		if persons:
			npersons = []
			for persond in persons:
				person_name = bm_extract.coerce_string(persond)
				if not person_name:
					person_name = bm_extract.as_string(persond, "name")
				if not person_name:
					continue

				npersond = {
					"name" : person_name,
				}

				for key in [ "uri", "email" ]:
					value = bm_extract.as_string(persond, key)
					if value:
						npersond[key] = value

				npersons.append(npersond)

			persons = npersons

		if not persons:
			try: del itemd[person_key]
			except: pass
		else:
			itemd[person_key] = persons

	def ScrubCategory(self, itemd):
		cats = bm_extract.as_list(itemd, "category")
		if cats:
			ncats = []
			for catd in cats:
				cat_name = bm_extract.coerce_string(catd)
				if not cat_name:
					cat_name = bm_extract.as_string(catd, "term")
				if not cat_name:
					continue

				ncatd = {
					"@term" : cat_name,
				}

				for key in [ "scheme", "label" ]:
					value = bm_extract.as_string(catd, key)
					if value:
						ncatd["@" + key] = value

				ncats.append(ncatd)

			cats = ncats

		if not cats:
			try: del itemd["category"]
			except: pass
		else:
			itemd["category"] = cats

	def ScrubLinks(self, itemd):
		links = bm_extract.as_list(itemd, "links")
		if links:
			nlinks = []
			for linkd in links:
				link_href = bm_extract.coerce_string(linkd)
				if not link_href:
					link_href = bm_extract.as_string(linkd, "href")
				if not link_href:
					continue

				nlinkd = {
					"@href" : link_href,
				}

				for key in [ "rel", "type", "hreflang", "title", "length", ]:
					value = bm_extract.as_string(linkd, key)
					if value:
						nlinkd["@" + key] = value

				nlinks.append(nlinkd)

			links = nlinks

		link = bm_extract.as_string(itemd, "link")
		if link:
			found = False
			for linkd in links:
				if link == bm_extract.as_string(linkd, "@href"):
					found = True
					break

			if not found:
				links.append({
					"@href" : link,
					"@rel" : "alternate",
				})

		for key in [ "link", "links" ]:
			try: del itemd[key]
			except: pass

		if links:
			itemd["link"] = links

if __name__ == '__main__':
	from bm_log import Log

	if False:
		api = RSS20()
		api.request = { "uri" : 'http://feeds.feedburner.com/DavidJanesCode' }
		for item in api.items:
			print "-", item['title']

		Log(meta = api.meta)

	if True:
		api = Feed()
		api.request = { "uri" : 'http://feeds.feedburner.com/DavidJanesCode' }
		for item in api.items:
			Log(item = item)

		Log(meta = api.meta)

	if False:
		writer = RSS20Writer()
		writer.items = [
			{
				"title" : "Post #1",
				"description" : "This is the data",
			},
		]
		writer.request = {
			"title" : "David Janes",
		}

		print writer.Produce()

	if False:
		api = Feed()
		api.request = { "uri" : 'http://feeds.feedburner.com/DavidJanesCode' }

		meta = api.meta
		del meta["link"]

		writer = RSS20Writer()
		writer.items = [ list(api.items)[0] ]
		writer.request = meta

		print writer.Produce()

