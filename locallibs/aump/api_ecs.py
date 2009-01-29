#
#   api_ecs.py
#
#   David Janes
#   2008.12.23
#
#	Copyright 2008 David Janes
#
#	Amazon Ecommerce
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

class AmazonECS(bm_api.APIReader):
	_base_query = {
		"Sort" : "relevancerank",
		"Operation" : "ItemSearch", 
		"Version" : "2008-08-19",
		"ResponseGroup" : [ "Small", ], 
	}
	_uri_base = "http://ecs.amazonaws.com/onca/xml"
	_meta_path = "Items.Request"
	_item_path = "Items.Item"
	_page_max_path = 'Items.TotalPages'
	_item_max_path = 'Items.TotalResults'
	_page_max = -1

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)

	def CustomizePageURI(self, page_index):
		if page_index == 1:
			return

		return	"%s=%s" % ( "ItemPage", page_index )

if __name__ == '__main__':
	api = AmazonECS(AWSAccessKeyId = os.environ["AWS_ECS_ACCESSKEYID"])
	api.SetRequest(
		Keywords = "Larry Niven",
		SearchIndex = "Books", 
		Condition = "New",
	)
	for item in api.IterItems():
		print "-", bm_extract.as_string(item, 'ItemAttributes.Title')
