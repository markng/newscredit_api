#
#	mfdict.py
#
#	David Janes
#	BlogMatrix
#	2006.11.26
#

import sys
import os
import pprint
import types
import re
import copy
import sets

from bm_log import Log

class mfdict(dict):
	"""A dictionary that can hold microformats

	Key concepts:
	- use "." separated subkeys
	- the new functions below can pull out partially matching subkeys
	- add will add multiple ( key, value ) pairs, event if 'key' appears multiple times
	"""
	def __init__(self, *av, **ad):
		dict.__init__(self, *av, **ad)
		self._count = 1

	def popitem(self, keys, otherwise = (None, None)):
		for item in self.finditems(keys):
			del self[item[0]]
			return	item

		return	otherwise

	def pop(self, keys, otherwise = None):
		return	self.popitem(keys, ( None, otherwise ))[1]

	def finditem(self, keys, otherwise = (None, None), exclude_keys = None):
		## returns the _least specific_ matching item (sorta)
		items = list(self.finditems(keys, exclude_keys = exclude_keys))
		if not items:
			return	otherwise

		items = map(lambda ( k, v ): ( len(k), k, v ), items)
		items.sort()

		return	items[0][1], items[0][2]

	def remove_ats(self):
		"""Remove all keys begining with '@'"""
		for key in self.keys():
			if key[:1] == '@':
				try: del self[key]
				except: pass

	def find(self, keys, otherwise = None):
		return	self.finditem(keys, ( None, otherwise ))[1]

	def finditems(self, keys, exclude_keys = None):
		if type(keys) in types.StringTypes:
			keys = keys.split(".")

		if type(exclude_keys) in types.StringTypes:
			exclude_keys = exclude_keys.split(".")
		elif not exclude_keys:
			exclude_keys = []

		for ( dkey, dvalue ) in self.iteritems():
			dkeys = dkey.split(".")

			found = True
			for key in keys:
				if key and key not in dkeys:
					found = False
					break

			xfound = False
			for xkey in exclude_keys:
				if xkey and xkey in dkeys:
					xfound = True
					break

			if found and not xfound:
				yield	dkey, dvalue

		raise	StopIteration

	def deepcopy(self):
		d = mfdict()
		for key, value in self.iteritems():
			d[key] = copy.deepcopy(value)

		return	d

	def add(self, keys, value):
		if type(keys) == types.ListType:
			keys = list(sets.Set(keys))
			keys = ".".join(keys)

		if self.has_key(keys):
			keys = "%s.%s" % ( keys, self._count )
			self._count += 1

		self[keys] = value

