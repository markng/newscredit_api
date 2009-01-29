#
#   api_postrank.py
#
#   David Janes
#   2009.01.23
#
#	Copyright 2009 David Janes
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
import bm_work

class SubscriptionManager(bm_api.APIBase):
	"""Composite API class"""

	def __init__(self, **ad):
		bm_api.APIBase.__init__(self, **ad)

	def SetRequest(self, **ad):
		bm_api.APIBase.SetRequest(self, **ad)

	def SetItems(self, items):
		bm_api.APIBase.SetRequest(self, **ad)

	def GetMeta(self):
		return	{}

	def IterItems(self):
		sapi = AllUserSubscriptions()
		for item in sapi.items:
			feed_hash = item.get('feed-hash')
			if not feed_hash:
				continue

			info = FeedInformation(feed_hash = feed_hash, _http_ad = { "min_retry" : 7 * 24 * 3600 })
			item.update(info.meta)

			yield	item

class AllUserSubscriptions(bm_api.APIReader):
	_uri_base = "http://www.postrank.com/myfeeds/subscriptions.xml"
	_item_path = "subscription"

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

class FeedInformation(bm_api.APIReader):
	_uri_base = None
	_item_path = "subscription"
	_required_properities = [ "feed_hash", ]
	_feed_hash = None

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def IterItems(self):
		raise	StopIteration

	@apply
	def feed_hash():
		def fget(self):
			return	self._feed_hash

		def fset(self, value):
			self._feed_hash = value
			self._uri_base = "http://api.postrank.com/v2/feed/%s/info?format=xml&appkey=postrank.com/example" % value

		return property(**locals())

class UserInformation(bm_api.APIReader):
	_uri_base = "http://www.postrank.com/user/info.json"
	_convert2work = bm_work.JSON2WORK()
	_item_path = ""

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

if __name__ == '__main__':
	import bm_oauth

	from bm_log import Log
	## Log.verbose = True

	bm_cfg.cfg.initialize()
	bm_oauth.OAuth(service_name = "postrank")

	bm_api.atom_like = True

	api = SubscriptionManager()

	for item in api.items:
		pprint.pprint(item)
