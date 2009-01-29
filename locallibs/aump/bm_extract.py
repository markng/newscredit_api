#
#   bm_extract.py
#
#   David Janes
#   2006.01.18
#
#	Extract data that's in the wrong format
#

import sys
import os
import os.path
import pprint
import time
import types
import re
import string

import datetime

class Marker:
	def __str__(self):
		return	"[[MARKER]]"

MARKER = Marker()
MARKER_OTHERWISE = Marker()

class AsIs:
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return	self.value

def is_dotpath_index(v):
	return	type(v) == types.IntType

def is_dotpath_key(v):
	return	type(v) in types.StringTypes

def is_list(o):
	return	isinstance(o, list) or type(o) == types.TupleType

def is_atomic(o):
	return	type(o) in [ types.StringType, types.UnicodeType, types.IntType, types.FloatType, types.BooleanType ]

def is_dict(o):
	return	isinstance(o, dict)

def is_none(o):
	return	o == None

def is_list_like(o):
	return	not is_dict(o) and not is_atomic(o) and (
		hasattr(o, "__getitem__") or
		type(o) in [ types.GeneratorType, types.XRangeType, ]
	)

def extract(o, path, otherwise = None):
	"""Extract data from a JSON-like object using a dot path. E.g.:

	- "value" -- o["value"]
	- "valued.value" -- o["valued"]["value"]
	- "values.5.value" -- o["values"][5]["value"]
	"""

	if not path:
		return	otherwise

	def _extract(o, items):
		if isinstance(o, AsIs):
			o = o.value

		from bm_log import Log
		if not items:
			return	o
		elif type(items[0]) == types.IntType:
			if type(o) in [ types.GeneratorType, types.XRangeType, ]:
				count = -1
				for subo in o:
					count += 1
					if count == items[0]:
						return	_extract(subo, items[1:])

				return	otherwise
			elif type(o) in [ types.ListType, types.TupleType ]:
				#
				#	[5] on a list indexes into the list.
				#	IndexError indicates no more list, and triggers otherwise
				#
				try:
					subo = o[items[0]]
				except IndexError:
					return	otherwise

				return	_extract(subo, items[1:])
			elif isinstance(o, dict):
				#
				#	[0] on a dictionary is ignored (i.e
				#		we treat dictionaries like [{...}]
				#	[N > 0] triggers otherwise
				#
				if items[0] == 0:
					return	_extract(o, items[1:])
				else:
					return	otherwise
			elif type(o) == types.InstanceType:
				#
				#	'o' is an object that is list-like
				#
				if hasattr(o, "__getitem__"):
					try:
						return	_extract(o.__getitem__(items[0]), items[1:])
					except IndexError:
						return	otherwise
					except:
						return	otherwise
				else:
					return	otherwise
			else:
				return	o
		elif type(items[0]) in types.StringTypes:
			if type(o) in [ types.GeneratorType, types.XRangeType, ]:
				for subo in o:
					return	_extract(subo, items)

				return	otherwise
			elif type(o) in [ types.ListType, types.TupleType ]:
				try:
					return	_extract(o[0], items)
				except IndexError:
					return	otherwise
			elif isinstance(o, dict):
				try:
					return	_extract(o[items[0]], items[1:])
				except KeyError:
					return	otherwise
			elif type(o) in [ types.InstanceType, types.ModuleType ]:
				#
				#	'o' is an object with this attribute, which may be a
				#	function of some sort
				#
				if hasattr(o, items[0]):
					attr = getattr(o, items[0])
					if type(attr) in [ types.MethodType, types.FunctionType, types.LambdaType ]:
						return	_extract(attr(), items[1:])
					else:
						return	_extract(attr, items[1:])
					
				#
				#	'o' is an object that is dictionary-like
				#
				if hasattr(o, "__getitem__"):
					try:
						return	_extract(o.__getitem__(items[0]), items[1:])
					except KeyError:
						return	otherwise
					except:
						return	otherwise
				else:
					return	otherwise
			else:
				return	otherwise
		else:
			assert(False), "programming error: items MUST be strings or ints"
		
	try:
		return	_extract(o, path_split(path))
	except:
		from bm_log import Log
		Log("PROGRAMMING ERROR EXCEPTION",
			path = path,
			o = o,
			exception = True,
		)
		raise

def as_int(o, path, otherwise = 0):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_int(d, otherwise = otherwise)

def as_bool(o, path, otherwise = False, **ad):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_bool(d, otherwise = otherwise, **ad)

def as_float(o, path, otherwise = 0):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_float(d, otherwise = otherwise)

def as_string(o, path, otherwise = "", separator = None, strip = False, at_key = '@'):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_string(d, separator = separator, otherwise = otherwise, strip = strip, at_key = at_key)

def as_datetime(o, path, otherwise = MARKER, separator = None, atom = False):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		if otherwise == MARKER:
			otherwise = datetime.datetime.now()
			if atom:
				otherwise = otherwise.isoformat()

		return	otherwise

	return	coerce_datetime(d, separator = separator, atom = atom)

def as_list(o, path, otherwise = MARKER_OTHERWISE, separator = None, strip = False, empties = True):
	if otherwise == MARKER_OTHERWISE:
		otherwise = []

	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_list(d, separator = separator, strip = strip, empties = empties)

def as_dict(o, path, otherwise = MARKER_OTHERWISE, at_key = '@'):
	if otherwise == MARKER_OTHERWISE:
		otherwise = {}

	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_dict(d, at_key = at_key)

def as_enum(o, path, enumeration, otherwise = None):
	d = extract(o, path, otherwise = MARKER)
	if d == MARKER:
		return	otherwise

	return	coerce_enum(d, enumeration = enumeration, otherwise = otherwise)

def search(o, paths, query, ignore_case = True, whole_words = False):
	"""Search multiple items in an an object, iden
	"""

	if not query or not paths or not o:
		return	True

	query = coerce_list(query, separator = " ", strip = True, empties = False)

	if ignore_case:
		query = map(lambda q: q.lower(), query)

	for path in paths:
		value = as_string(o, path)
		if not value:
			continue

		if ignore_case:
			value = value.lower()

		for q in list(query):
			if value.find(q) > -1:
				query.remove(q)

		if not query:
			return	True

	return	False

def coerce_dict(value, otherwise = MARKER_OTHERWISE, at_key = '@'):
	if otherwise == MARKER_OTHERWISE:
		otherwise = {}

	if isinstance(value, dict):
		return	value

	if at_key == None:
		return	otherwise

	return	{
		at_key : value
	}
			
def coerce_enum(value, enumeration, otherwise = None):
	value = coerce_string(value)
	if value in enumeration:
		return	value
	else:
		return	otherwise
			
def coerce_string(value, otherwise = "", separator = None, strip = False, at_key = '@'):
	import bm_text

	if isinstance(value, dict):
		value = value.get(at_key)

	while True:
		if isinstance(value, AsIs):
			value = value.value
			continue

		if is_list_like(value):
			value = list(value)

		if is_list(value):
			if not value:
				return	otherwise

			if separator != None:
				value = separator.join(map(lambda v: coerce_string(v, strip = strip, at_key = at_key), value))
				if strip:
					value = value.strip()

				return	value

			value = value[0]
			continue
		elif is_dict(value):
			if value.has_key(at_key):
				value = value.get(at_key)
				continue
			else:
				return	otherwise

		break

	if value == None:
		return	otherwise

	value = bm_text.tounicode(value)
	if strip:
		value = value.strip()

	return	value

def coerce_int(value, otherwise = 0):
	try:
		while type(value) in [ types.ListType, types.TupleType, ]:
			if not value:
				return	otherwise

		if value == None:
			return	otherwise
		elif type(value) in types.StringTypes:
			dotx = value.find('.')
			if dotx > -1:
				value = value[:dotx]

			return	int(value)
		else:
			return	int(value)
	except TypeError:
		return	otherwise
	except ValueError:
		return	otherwise

def coerce_float(value, otherwise = 0):
	try:
		if type(value) in [ types.ListType, types.TupleType, ]:
			if value:
				return	float(value[0])
			else:
				return	otherwise
		elif value == None:
			return	otherwise
		else:
			return	float(value)
	except TypeError:
		return	otherwise
	except ValueError:
		return	otherwise

def coerce_list(value, otherwise = MARKER_OTHERWISE, separator = None, strip = False, empties = True):
	if otherwise == MARKER_OTHERWISE:
		otherwise = []

	result = None

	if type(value) in [ types.ListType, types.GeneratorType, types.XRangeType, ]:
		result = list(value)
	elif hasattr(value, "__iter__") and not isinstance(value, dict):
		result = list(value)
	elif type(value) == types.NoneType:
		return	otherwise
	elif separator and type(value) in types.StringTypes:
		result = value.split(separator)
	else:
		result = [ value ]

	assert(type(result) == types.ListType)

	if strip:
		result = map(lambda s: s.strip(), result)

	if not empties:
		result = filter(lambda s: s, result)

	return	result

def coerce_bool(value, otherwise = False, trues = None, falses = None):
	"""
	Rules for coercing to a Bool:
	- if 'trues' provided, and value present: True
	- if 'false' provided, and value present: False
	- if a non-empty list or tuple: True
	- None: otherwise
	- not value: False
	- value can be translated to an int: int(value)
	- finally: True
	"""

	if trues == None:
		trues = [ "t", "true", "y", "yes", "1", 1 ]

	if falses == None:
		falses = [ "f", "false", "n", "no", "0", 0 ]

	try:
		if type(value) is types.BooleanType:
			return value
		elif trues and value in trues:
			return	True
		elif trues and type(value) in types.StringTypes and value.lower() in trues:
			return	True
		elif falses and value in falses:
			return	False
		elif falses and type(value) in types.StringTypes and value.lower() in falses:
			return	False
		elif type(value) in [ types.ListType, types.TupleType, ]:
			if value:
				return	True
			else:
				return	otherwise
		elif value == None:
			return	otherwise
		elif not value:
			return	otherwise
		else:
			try:
				return	bool(int(value))
			except:
				return	True
	except TypeError:
		return	otherwise
	except ValueError:
		return	otherwise

def coerce_datetime(value, otherwise = MARKER, atom = False, rfc822 = False, **ad):
	result = otherwise

	if isinstance(value, datetime.datetime):
		if atom:
			value = value.isoformat()
		elif rfc822:
			value = value.strftime("%a, %d %b %Y %H:%M:%S %z")

		return	value

	try:
		import pytz
		import dateutil.parser

		dt = dateutil.parser.parse(value)
		if dt:
			result = dt
	except:
		pass

	if result == MARKER:
		result = datetime.datetime.now()

	if result:
		if result.tzinfo == None:
			result = result.replace(tzinfo = pytz.UTC)

	if isinstance(result, datetime.datetime):
		if atom:
			result = result.isoformat()
		elif rfc822:
			result = result.strftime("%a, %d %b %Y %H:%M:%S %z")

	return	result

def set(o, path, value):
	parts = path_split(path)
	if not parts:
		return

	heads, tail = parts[:-1], parts[-1]

	#
	#	Work your way through the data structure,
	#	indexing through each subdictionary. If there's
	#	a path and no dictionary, make one
	#
	last_head = None
	last_o = None

	for head in heads:
		this_o = o

		if is_dotpath_key(head):
			## ... this block doesn't do anything until we support indicies ...
			if not isinstance(o, dict):
				o = dict()
				if last_o:
					last_o[last_head] = o

			s = o.get(head)
			if isinstance(s, dict):
				o = s
			else:
				s = dict()
				o[head] = s
				o = s
		elif is_dotpath_index(head):
			raise	KeyError, "indicies not supported"
		else:
			raise	AssertionError, "can't happen"

		last_head = head
		last_o = this_o

	o[tail] = value

#
#	Path stuff below here
#
def path_split(path):
	"""Split a 'meta.searchlinks.link[0].xxx[5]' style path"""
	return	list(PathSplitter(path))

key_re = "(?P<path>[-:@$a-z0-9_]+)"	# ... really need to make a generous & ungenerous version
key_rex = re.compile(key_re, re.I)

index_re = "[[](?P<index>[0-9]+)[]]"
index_rex = re.compile(index_re, re.I)

NIL = ( None, None, None )

class PathSplitter:
	def __init__(self, path, exception = True):
		self.opath = path
		self.path = path
		self.exception = exception

		assert(type(path) in types.StringTypes)

	def __iter__(self):
		state = self.state_key

		while state:
			( result_value, next_state, next_path ) = state()
			if result_value != None:
				yield result_value

			state = next_state

			if next_path != None:
				self.path = next_path

		if self.exception and self.path:
			raise	KeyError, "not all path consumed ('%s' -> '%s')" % ( self.opath, self.path, )

	def state_key(self):
		key_match = key_rex.match(self.path)
		if not key_match:
			return	NIL

		return	key_match.group('path'), self.state_dot_or_index, self.path[key_match.end():]

	def state_dot_or_index(self):
		if self.path[:1] == '.':
			return	None, self.state_key, self.path[1:]
		elif self.path[:1] == '[':
			if self.path[:2] == '["' or self.path[:2] == "['":
				return	None, self.state_quoted_key, self.path
			elif self.path[1:2] in string.digits:
				return	None, self.state_index, self.path
		else:
			return	NIL

	def state_index(self):
		index_match = index_rex.match(self.path)
		if not index_match:
			return	NIL

		return	int(index_match.group('index')), self.state_dot_or_index, self.path[index_match.end():]

	def state_quoted_key(self):
		end = self.path[1] + ']'
		index = 2
		result = None

		while True:
			next = self.path.find(end, index)
			if next == -1:
				break

			if self.path[next - 1] != '\\':
				result = self.path[1:next + 1]
				break

			if self.path[next - 2] != '\\':
				result = self.path[1:next + 1]
				break

			index = next + 1

		if result == None:
			return	NIL

		return	eval(result), self.state_dot_or_index, self.path[next + 2:]

if __name__ == '__main__':
	pass
