#
#   api_delicious.py
#
#   David Janes
#   2009.01.13
#
#	Copyright 2009 David Janes
#
#	Interface to Del.icio.us
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

"""
http://delicious.com/help/api

Posts

* posts/add - add a new bookmark
* posts/delete - delete an existing bookmark
* posts/get - get bookmark for a single date, or fetch specific items
* posts/dates - list dates on which bookmarks were posted
* posts/recent - fetch recent bookmarks
* posts/all - fetch all bookmarks by date or index range
* posts/all?hashes - fetch a change detection manifest of all items
"""

class Delicious(bm_api.APIReader):
	_convert2work = bm_work.XML2WORK(keep_attributes = True, attribute_prefix = '')
	_meta_removes = [ "post" ]
	_atom_item = {
		"content" : "extended", 
		"title" : "description",
		"link" : "href",
		"id" : "hash",
	}

	def ArgumentList(self, value):
		if value:
			value = bm_extract.coerce_list(value)
			value = map(urllib.quote, value)
			value = bm_extract.coerce_string(value, separator = " ")
			value = bm_extract.AsIs(value)

		return	value

	def ArgumentDate(self, dt):
		if dt:
			dt = bm_extract.coerce_datetime(dt, otherwise = None)
			if dt:
				return	"%sZ" % dt.isoformat()[:19]

	def CustomizeAtomItem(self, itemd):
		try:
			itemd["updated"] = itemd.pop("time").rstrip("Z") + "+0000"
		except KeyError:
			pass

		cats = []
		for tag in bm_extract.as_list(itemd, "tag", separator = " "):
			cats.append({ "term" : tag })

		if cats:
			itemd["category"] = cats

		try: del itemd["tag"]
		except KeyError: pass

		return	bm_api.APIReader.CustomizeAtomItem(self, itemd)

	def CustomizeAtomMeta(self, itemd):
		try:
			tag = itemd.pop('tag')
		except KeyError:
			tag = None

		try:
			itemd["link"] = "http://delicious.com/%s/" % itemd["user"]
		except KeyError:
			pass

		try:
			itemd["title"] = "%s: %s" % ( itemd.pop("user"), tag )
		except KeyError:
			pass

		try:
			itemd["updated"] = itemd.pop("dt").rstrip("Z") + "+0000"
		except KeyError:
			pass

		return	itemd


class PostsList(Delicious):
	"""Use this to list posts ... eventually we'll make sure it iterates through every post"""

	_uri_base = "https://api.del.icio.us/v1/posts/recent"
	_item_path = "post"

	def __init__(self, tag = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(tag = tag, count = 100)

class PostsRecent(Delicious):
	_uri_base = "https://api.del.icio.us/v1/posts/recent"
	_item_path = "post"

	def __init__(self, tag = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(tag = tag)

class PostsDates(Delicious):
	_uri_base = "https://api.del.icio.us/v1/posts/dates"
	_item_path = "post"

	def __init__(self, tag = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(tag = tag)

class PostsHashes(Delicious):
	_uri_base = "https://api.del.icio.us/v1/posts/all?hashes"
	_item_path = "post"

	def __init__(self, tag = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(tag = tag)

class PostsAll(Delicious):
	_uri_base = "https://api.del.icio.us/v1/posts/all?meta=yes"
	_item_path = "post"

	def __init__(self, tag = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(tag = tag, results = 20)

class PostsGet(Delicious):
	_uri_base = "https://api.del.icio.us/v1/posts/get?meta=yes"
	_item_path = "post"

	def __init__(self, tag = None, dt = None, url = None, hashes = None, **ad):
		Delicious.__init__(self, **ad)

		self.SetRequest(
			tag = self.ArgumentList(tag),
			url = url,
			dt = self.ArgumentDate(dt),
			hashes = self.ArgumentList(hashes),
		)

if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	from bm_log import Log
	Log.verbose = True

##	username = bm_cfg.cfg.as_string('delicious.username')
##	if username:
##		bm_uri.Authenticate.Global().Add(
##			"https://api.del.icio.us",
##			bm_uri.AuthBasic(
##				username = username,
##				password = bm_cfg.cfg.as_string('delicious.password', otherwise = ''),
##			)
##		)

	bm_api.atom_like = True

	api = PostsList(tag = 'python', authenticate = 'delicious')
	# api = PostsRecent()
	# api = PostsDates(tag = 'python')
	# api = PostsHashes(tag = 'python')
	# api = PostsGet(tag = [ "funny", ])
	# api = PostsAll()

	for item in api.items:
		pprint.pprint(item)

	pprint.pprint(api.meta)
