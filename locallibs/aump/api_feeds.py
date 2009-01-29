#
#   api_feeds.py
#
#   David Janes
#   2009.01.17
#
#	Copyright 2009 David Janes
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
import bm_feedparser
import api_microformat

from bm_log import Log

import microformat
import hdocument

class OneFeed(api_microformat.SimpleMicroformat):
	"""A feed-finder like function
	- rss feeds
	- page title
	- page URI

	The result is returned in both the 'meta' and 'items'.
	"""

	_parser_class = hdocument.MicroformatDocument
	_parserd = {
		'do_feed' : True, 
		'do_h' : False, 
		'do_img' : False, 
		'do_a' : False, 
		'do_title' : False, 
	}

	def Fetch(self):
		result = {}

		#
		#	First, assume it's a feed and see what we find
		#
		self._FetchFeed(self.uri, result)

		#
		#	If there's no 'link', it wasn't a feed ... treat it like a page
		#
		if not result.get('link'):
			self._FetchPage(self.uri, result)

			#
			#	If that page has an RSS feed, then use _that_ as a basis to find the home
			#
			feed = bm_extract.as_string(result, "links[0].href")
			if feed:
				result_old = result

				result = {}
				self._FetchFeed(feed, result)

				if not result.get('link'):
					result = result_old

		#
		#	Return the result as both items and in meta
		#
		self._ScrubLinks(result)

		self._items = [ result ]
		self._meta = result

	def _FetchFeed(self, uri, result):
		#
		#	Use the URI as a feed
		#
		try:
			feed = bm_feedparser.parse(uri)
			feed_feed = feed["feed"]
			feed_link = bm_feedparser.feedparser_get(feed_feed, "link") or ""
		except:
			Log("unexpected error in feedparser - ignoring", uri = uri, exception = True)
			return

		if not feed_link:
			return

		result["link"] = feed_link
		result["title"] = bm_feedparser.feedparser_get(feed_feed, "title") or ""

		#
		#	Add all the RSS feeds that were found
		#
		links = []
		for linkd in feed_feed.get("links") or []:
			href = linkd.get('href')
			rel = linkd.get('rel')
			type = linkd.get('type')

			if not href:
				continue

			if rel == 'self':
				linkd["rel"] = "alternate"
				links.append(linkd)
				continue

			if type == 'text/html':
				continue

			if type in [ "application/rss+xml", "application/atom+xml", ]:
				linkd["rel"] = "alternate"
				links.append(href)
				continue

		if links:
			result["links"] = links
		else:
			result["links"] = [{
				"href" : uri,
				"rel" : "alternate",
			}]

	def _ScrubLinks(self, result):
		links = result.get("links")
		if not links:
			return

		for linkd in links:
			href = bm_extract.as_string(linkd, "href")
			type = bm_extract.as_string(linkd, "type")

			if not href or type:
				continue

			if href.endswith(".atom"):
				linkd["type"] = "application/atom+xml"
			elif href.endswith(".rss") or href.endswith(".xml"):
				linkd["type"] = "application/rss+xml"
			elif href.find("feedburner.com") > -1:
				linkd["type"] = "application/rss+xml"

	def _FetchPage(self, uri, result):
		try:
			try:
				self.uri = uri
				api_microformat.SimpleMicroformat.Fetch(self)
			finally:
				uri = self.uri

			result["link"] = uri
			result["title"] = self._parser.document_title

			links = []
			for feedd in self._items[0]["feed"]:
				href = feedd["src"]
				links.append({
					"href": href,
					"rel" : "alternate"
				})

			if links:
				result["links"] = links
		except microformat.MicroformatError:
			pass

class ManyFeeds(bm_api.APIBase):
	require_feed = False

	def __init__(self, **ad):
		bm_api.APIBase.__init__(self, **ad)

	def IterItems(self):
		for item in self._request_items:
			link = bm_extract.as_string(item, "link")
			if not link:
				continue

			try:
				itemd = OneFeed(uri = link).meta
				if not self.require_feed or itemd.get("links"):
					yield	itemd
			except bm_uri.DownloaderError:
				Log("ignoring unwanted exception", uri = link, exception = True)

if __name__ == '__main__':
	import bm_cfg
	bm_cfg.cfg.initialize()

	if False:
		api = OneFeed()
		api.request = {
			"uri" : "http://code.davidjanes.com/blog/"
		}

		for item in api.items:
			pprint.pprint(item, width = 1)

	if False:
		api = OneFeed()
		api.request = {
			"uri" : "http://code.davidjanes.com/blog/2009/01/23/transparently-working-with-oauath/",
		}

		pprint.pprint(api.response, width = 1)


	if False:
		api = ManyFeeds()
		api.items = [
			{
				"link" : "http://feeds.feedburner.com/DavidJanesCode",
			},
			{
				"link" : "http://code.davidjanes.com/blog/2009/01/23/transparently-working-with-oauath/",
			},
			{
				"link" : "http://code.davidjanes.com/",
			},
			{
				"link" : "http://bletch.example.com/",
			},
		]
		for item in api.items:
			pprint.pprint(item, width = 1)

	if True:
		username = bm_cfg.cfg.as_string('delicious.username')
		if username:
			bm_uri.Authenticate.Global().Add(
				"https://api.del.icio.us",
				bm_uri.AuthBasic(
					username = username,
					password = bm_cfg.cfg.as_string('delicious.password', otherwise = ''),
				)
			)


		bm_uri.config["min_retry"] = 24 * 3600
		Log.verbose = True

		import api_delicious
		import api_opml

		api_delicious = api_delicious.PostsList(tag = "python django", _authenticate = "delicious")
		api_many = ManyFeeds(require_feed = True)
		api_opml = api_opml.OPMLWriter()

		api_many.items = api_delicious.items
		api_opml.items = api_many.items

		print api_opml.Produce()
