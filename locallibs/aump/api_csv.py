#
#   api_csv.py
#
#   David Janes
#   2008.12.23
#
#	Copyright 2008 David Janes
#
#	Read CSV as Work objects
#

import os
import sys
import urllib
import types
import pprint
import types
import csv
import cStringIO as StringIO

try:
	import json
except:
	import simplejson as json

import bm_extract
import bm_uri
import bm_api
import bm_work

from bm_log import Log

class CSV(bm_api.APIReader, bm_work.Sluggifier):
	_uri_param = True
	_item_path = "items"

	_column_names = []
	_column_rows = None
	_skip_rows = 0
	_max_rows = sys.maxint
	_properties = [ "uri", "column_names", "column_rows", "max_rows", "skip_rows", ]

	def __init__(self, **ad):
		bm_api.APIReader.__init__(self, **ad)
		bm_work.Sluggifier.__init__(self)
	
		self._convert2work = self

	@apply
	def column_rows():
		def fset(self, r):
			if type(r) in [ types.ListType, types.TupleType ]:
				if len(r) == 1:
					self._column_rows = ( r[0], r[0], )
				elif len(r) >= 2:
					self._column_rows = ( r[0], r[1], )
			else:
				self._column_rows = ( r, r )

		return property(**locals())

	@apply
	def max_rows():
		def fset(self, n):
			self._max_rows = n

		return property(**locals())

	@apply
	def skip_rows():
		def fset(self, n):
			self._skip_rows = n

		return property(**locals())

	@apply
	def column_names():
		def fset(self, names):
			self.AddColumnNames(bm_extract.coerce_list(names))

		return property(**locals())

	def FeedString(self, raw):
		items = []
		rd = {
			"items" : items,
		}
		reader = csv.reader(StringIO.StringIO(raw))

		count = 0
		for row in reader:
			count += 1

			if self._column_rows:
				if count >= self._column_rows[0] and count <= self._column_rows[1]:
					self.AddColumnNames(row)
					continue

			if count <= self._skip_rows:
				continue

			itemd = dict(
				zip(
					map(self.GetColumnName, xrange(len(row))),
					row
				)
			)
			self.SluggifyObject(itemd)
			items.append(itemd)

			if len(items) == self._max_rows:
				break
			
		return	rd

	def AddColumnNames(self, row):
		while len(self._column_names) < len(row):
			self._column_names.append("")

		index = -1
		for name in row:
			index += 1

			if row[index] and not self._column_names[index]:
				self._column_names[index] = row[index]

	def GetColumnName(self, index):
		if index < len(self._column_names) and self._column_names[index]:
			return	self._column_names[index]

		return	"C%d" % index

	def GetMeta(self):
		return	{}

if __name__ == '__main__':
	api = CSV()
	api.request = {
		"uri" : 'http://www.census.gov/popest/states/tables/NST-EST2006-01.csv',
		"column_rows" : ( 3, 4, ),
		"skip_rows" : 9,
		"max_rows": 51,
	}
	pprint.pprint(list(api.items))
	pprint.pprint(api.meta)
