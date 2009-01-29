#
#   bm_cfg.py
#
#   David Janes
#   2006.01.08
#
#	Globally find and load configurations
#

import pprint
import sys
import os
import os.path
import types

try:
	import json
except ImportError:
	import simplejson as json

import bm_io
import bm_extract

from bm_log import Log

IS_CHANGED = "@Changed"
IS_PUBLIC = "@Public"
PATH = "@Path"

class CfgBase(object):
	"""To simplify the task of people wanting to derive their own Cfg"""

	def get(self, path, **ad):
		return	bm_extract.extract(self.private, path, **ad)

	def as_float(self, path, **ad):
		return	bm_extract.as_float(self.private, path, **ad)

	def as_int(self, path, **ad):
		return	bm_extract.as_int(self.private, path, **ad)

	def as_bool(self, path, **ad):
		return	bm_extract.as_bool(self.private, path, **ad)

	def as_list(self, path, **ad):
		return	bm_extract.as_list(self.private, path, **ad)

	def as_dict(self, path, **ad):
		return	bm_extract.as_dict(self.private, path, **ad)

	def as_string(self, path, **ad):
		return	bm_extract.as_string(self.private, path, **ad)

	def as_enum(self, path, **ad):
		return	bm_extract.as_num(self.private, path, **ad)

	def initialize(self):
		"""Initialize values the in the standard way (whatever that may mean)"""
		pass

class Cfg(CfgBase):
	_cfg_private = {}
	_cfg_public = {}

	@apply
	def public():
		def fget(self):
			return	self._cfg_public

		return property(**locals())

	@apply
	def private():
		def fget(self):
			return	self._cfg_private

		return property(**locals())

	def add_by_key(self, key, value, is_public = False):
		self.add({ key : value }, is_public = is_public)

	def add(self, d, is_public = False):
		if type(d) != types.DictType:
			raise TypeError("only dictionaries can be added")

		if d.get(IS_PUBLIC) or is_public:
			#
			#	Public definitions never overwrite private definitions
			#
			for key, value in d.iteritems():
				if type(value) != types.DictType:
					continue

				if not self._cfg_private.has_key(key):
					self._cfg_private[key] = value

				self._cfg_public[key] = value
		else:
			self._cfg_private.update(d)

	def load(self, path, exception = False, depth = 0):
		try:
			if os.path.isdir(path) and depth < 2:
				for file in os.listdir(path):
					self.load(os.path.join(path, file))
			elif os.path.isfile(path):
				if path.endswith(".json"):
					d = json.loads(bm_io.readfile(path))
					if type(d) != types.DictType:
						raise TypeError("only dictionaries can be added")

					for key, subd in d.iteritems():
						if isinstance(subd, dict):
							subd[PATH] = path
							subd[IS_CHANGED] = False

					self.add(d)

		except:
			if exception:
				raise

			Log("ignoring exception", exception = True, path = path)

	def initialize(self):
		"""Initialize values the in the standard way (whatever that may mean)"""

		cfg_dir = self.GetDirectory()
		if cfg_dir:
			self.load(cfg_dir)
			return

	def GetDirectory(self):
		"""Get the directory to store CFG in"""

		#
		#	Coded in the environment
		#
		cfg_dir = os.environ.get("BM_CFG_DIR")
		if cfg_dir:
			if not os.path.exists(cfg_dir):
				try: os.makedirs(cfg_dir)
				except: pass

			if os.path.exists(cfg_dir):
				return	cfg_dir

		#
		#	In our home directory
		#
		home_dir = os.environ.get("HOME")
		if home_dir:
			cfg_dir = os.path.join(home_dir, ".cfg")

			if not os.path.exists(cfg_dir):
				try: os.makedirs(cfg_dir)
				except: pass

			if os.path.exists(cfg_dir):
				return	cfg_dir

		#
		#	In the current directory
		#
		cfg_dir = os.path.join(".", ".cfg")
		if os.path.exists(cfg_dir):
			return	cfg_dir

	def Save(self):
		for key, d in self.private.iteritems():
			if not isinstance(d, dict):
				continue

			if not d.get(IS_CHANGED):
				continue

			if not d.get(PATH):
				d[PATH] = os.path.join(self.GetDirectory(), "%s.json" % key)


			#
			#	This is the version we are going to persist
			#
			nd = {}
			for subkey, subvalue in d.iteritems():
				if subkey.startswith("@"):
					continue

				nd[subkey] = subvalue

			#
			#	Save, preserving old data
			#
			wd = json.loads(bm_io.readfile(d[PATH]))
			wd[key] = nd

			bm_io.AtomicWrite(filename = d[PATH], data = json.dumps(wd, indent = 4, sort_keys = True))

			Log("saved partial cfg", filename = d[PATH], keys = wd.keys())

cfg = Cfg()
		
if __name__ == '__main__':
	cfg.initialize()

	for file in sys.argv[1:]:
		cfg.load(file)

	pprint.pprint({
		"private" : cfg.private,
		"public" : cfg.public,
	}, width = 1)

