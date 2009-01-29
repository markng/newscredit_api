#
#   api_bitly.py
#
#   David Janes
#   2009.01.22
#
#	Copyright 2009 David Janes
#
#	Interface to Bit.ly
#	http://www.bit.ly/
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

class Shorten(bm_api.APIReader):
	_uri_base = "http://api.bit.ly/shorten"
	_base_query = {
		"version" : "2.0.1",
		"format" : "json",
	}
	_convert2work = bm_work.JSON2WORK()
	_item_path = ""
	_required_attributes = [ "longUrl", ]

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def CustomizeRestart(self):
		username = bm_cfg.cfg.as_string('bitly.username')
		if username:
			self._request_meta["login"] = username

		api_key = bm_cfg.cfg.as_string('bitly.api_key')
		if api_key:
			self._request_meta["apiKey"] = api_key

if __name__ == '__main__':
	bm_cfg.cfg.initialize()
	bm_uri.AuthBasic(service_name = 'bitly', api_uri = "http://api.bit.ly")

	from bm_log import Log
	Log.verbose = True

	bm_api.atom_like = True

	api = Shorten(longUrl = "http://www.davidjanes.com")
	pprint.pprint(api.meta)
