#
#   api_fireeagle.py
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

class User(bm_api.APIReader):
	_uri_base = 'https://fireeagle.yahooapis.com/api/0.1/user.json?format=json'
	_convert2work = bm_work.JSON2WORK()
	_item_path = "user.location_hierarchy"
	_atom_item = {
		u"title" : "name"
	}

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def GetMeta(self):
		d = bm_extract.as_dict(bm_api.APIReader.GetMeta(self), "user.location_hierarchy[0]")

		if self.AtomLike():
			d = self.CustomizeAtomItem(d)

		return	d

	def CustomizeAtomItem(self, d):
		d = bm_api.APIReader.CustomizeAtomItem(self, d)

		if bm_extract.as_string(d, "geometry.type") == "Point":
			coordinates = bm_extract.as_list(d, "geometry.coordinates")
			if len(coordinates) >= 2:
				bm_api.add_latlon(d, coordinates[0], coordinates[1])

			try: del d["geometry"]
			except: pass

		return	d

if __name__ == '__main__':
	import bm_oauth

	from bm_log import Log
	Log.verbose = True

	bm_cfg.cfg.initialize()
	bm_oauth.OAuth(service_name = "fireeagle")

	bm_api.atom_like = True

	api = User()

	pprint.pprint(api.meta)
