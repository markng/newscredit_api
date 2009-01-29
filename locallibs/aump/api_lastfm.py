#
#   api_lastfm.py
#
#   David Janes
#   2008.11.22
#
#	Copyright 2008 David Janes
#
#	Interface to Last.FM
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

class Artist(bm_api.APIReader):
	"""
	See: http://www.last.fm/api/show?service=272
	"""

	_base_uri = "http://ws.audioscrobbler.com/2.0/"
	_atom_item = {
		"title" : "name", 
		"id" : "mbid", 
		"link" : "url", 
	}

	def __init__(self, **ad):
		ad["method"] = "artist.getinfo"
		ad["uri"] = "http://ws.audioscrobbler.com/2.0/"

		bm_api.APIReader.__init__(self, **ad)

	def CustomizeRestart(self):
		if not self._request_meta.get('api_key'):
			self._request_meta['api_key'] = bm_cfg.cfg.as_string('lastfm.api_key')

	def CustomizePageURI(self, page_index):
		if page_index > 1:
			return	"page=%s" % page_index

	def CustomizeAtomItem(self, d):
		d = bm_api.APIReader.CustomizeAtomItem(self, d)
		
		images = bm_extract.as_list(d, "image")
		if images:
			images = map(lambda i: i.strip(">"), images)	## common last.fm bug
			d["images"] = images
			d["photo"] = images[-1]

		content = bm_extract.as_string(d, "bio.content")
		if content:
			d["content"] = content

			try: del d["bio"]
			except: pass

		return	d

class ArtistEvents(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "events.event"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.getevents",
	}

class ArtistInfo(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "artist"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.getinfo",
	}

class ArtistSimilar(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "similarartists.artist"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.getsimilar",
	}

class ArtistTags(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "tags.tag"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.gettags",
	}

class ArtistTopAlbums(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "topalbums.album"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.gettopalumns",
	}

class ArtistTopFans(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "topfans.user"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.gettopfans",
	}

class ArtistTopTags(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "toptags.tag"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.gettoptags",
	}

class ArtistTopTracks(Artist):
	_page_max = -1
	_page_max_path = None
	_item_path = "toptracks.track"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.gettoptracks",
	}

class ArtistSearch(Artist):
	_page_max = -1
	_page_max_path = "results.totalResults"
	_item_path = "artist"
	_required_attributes = [ "artist", ]
	_base_query = {
		"method" : "artist.search",
	}

if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	from bm_log import Log
	Log.verbose = True

	try:
		import json
	except:
		import simplejson as json

	action = "artist.getInfo"
	if len(sys.argv) > 1:
		action = sys.argv[1]

	query = 'Nickeback'

	if action == "artist.getEvents":
		api = ArtistEvents(artist = query)
	elif action == "artist.getInfo":
		api = ArtistInfo(artist = query)
	elif action == "artist.getSimilar":
		api = ArtistSimilar(artist = query)
	elif action == "artist.getTags":
		api = ArtistTags(artist = query)
	elif action == "artist.getTopAlbums":
		api = ArtistTopAlbums(artist = query)
	elif action == "artist.getTopFans":
		api = ArtistTopFans(artist = query)
	elif action == "artist.getTopTags":
		api = ArtistTopTags(artist = query)
	elif action == "artist.getTopTracks":
		api = ArtistTopTracks(artist = query)
	elif action == "artist.search":
		api = ArtistSearch(artist = query)
	else:	
		api = None

	if api:
		any = False

		for item in api.items:
			any = True
			print json.dumps(item, indent = 1)

##		if not any:
##			pprint.pprint(api.response)

	else:
		print >> sys.stderr, "no query?"
