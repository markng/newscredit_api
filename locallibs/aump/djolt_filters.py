#
#	djolt_filters.py
#	- djolt - Django-like templates
#
#	David Janes
#	2008-11-26
#
#	djolt - Django-like templates
#
#	Standard filters for Djolt
#

import sys
import os
import re
import random
import urllib
import string

try:
	import json
except ImportError:
	import simplejson as json

from bm_log import Log

import bm_extract
import bm_work

import djolt_base

sluggie_rex = re.compile(u"[^a-z0-9]", re.I|re.DOTALL)
dash_rex = re.compile("-+")
underscore_rex = re.compile("_+")

#
#	Custom - wrap whatever the value is in an 'AsIs' object.
#	If that is at the front of the result when rendering,
#	we don't convert to a string - we keep it the way it is
#
class Filter_raw(djolt_base.Filter):
	_name = "raw"

	def Filter(self, name, argument, value):
		return	bm_extract.AsIs(value)

Filter_raw()

#
#	Custom - escape a string to be JS friendly
#
class Filter_escapejs(djolt_base.Filter):
	_name = "escapejs"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		value = json.dumps(value, cls = bm_work.IterEncoder)[1:-1]

		return	value

Filter_escapejs()

#
#	Custom: produce a slug that is Javascript friendly (for identifiers, variables)
#
class Filter_jslug(djolt_base.Filter):
	_name = "jslug"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		value = sluggie_rex.sub("_", value)
		value = underscore_rex.sub("_", value)
		value = value.strip("_")
		value = value.lower()

		return	value

Filter_jslug()

#
#	Custom: return object as a JSON string
#
class Filter_json(djolt_base.Filter):
	"""Return compressed JSON"""
	_name = "json"

	def Filter(self, name, argument, value):
		return	json.dumps(value, cls = bm_work.IterEncoder)

Filter_json()

#
#	Custom: return object as a pretty-printed JSON string
#
class Filter_pjson(djolt_base.Filter):
	"""Return pretty-printed JSON"""
	_name = "pjson"

	def Filter(self, name, argument, value):
		return	json.dumps(value, indent = 2, sort_keys = True, cls = bm_work.IterEncoder)

Filter_pjson()

#
#	Custom: pythonic-strip
#
class Filter_strip(djolt_base.Filter):
	"""Python 'strip' command"""

	_name = "strip"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		if argument:
			return	value.strip(argument)
		else:
			return	value.strip()

Filter_strip()

#
#	Custom: pythonic-rstrip
#
class Filter_rstrip(djolt_base.Filter):
	"""Python 'rstrip' command"""

	_name = "rstrip"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		if argument:
			return	value.rstrip(argument)
		else:
			return	value.rstrip()

Filter_rstrip()

#
#	Custom: pythonic-lstrip
#
class Filter_lstrip(djolt_base.Filter):
	"""Python 'lstrip' command"""

	_name = "lstrip"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		if argument:
			return	value.lstrip(argument)
		else:
			return	value.lstrip()

Filter_lstrip()

#
#	Custom: pythonic-split
#
class Filter_split(djolt_base.Filter):
	"""Python 'split' command - break a string into component parts"""

	_name = "split"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		if argument:
			return	value.split(argument)
		else:
			return	value.split()

Filter_split()

#
#	Return the n-th item a list
#
class Filter_atindex(djolt_base.Filter):
	_name = "atindex"

	def Filter(self, name, argument, value):
		"""
		Example:

			{{ value|atindex:1 }}

		If value is the list ['a', 'b', 'c'], the output will be 'b'.
		If called without an argument, we assume 0.
		"""

		value = bm_extract.coerce_list(value, separator = None)
		index = bm_extract.coerce_int(argument)

		if index < len(value):
			return	value[index]

Filter_atindex()

#
#	Pythonic string.capitalize
#
class Filter_capitalize(djolt_base.Filter):
	_name = "capitalize"

	def Filter(self, name, argument, value):
		"""\
		Make the first letter uppercase, the rest lower

		For example:

			{{ value|capitalize }}

		If value is "Joel is a slug", the output will be "Joel is a slug".
		"""
		value = bm_extract.coerce_string(value, separator = None)
		if value:
			return	string.capwords(value)

Filter_capitalize()

#
#	Django standard items below here
#
class Filter_add(djolt_base.Filter):
	_name = "add"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_int(value, otherwise = 0)
		argument = bm_extract.coerce_int(argument, otherwise = 0)

		return	"%d" % ( value + argument )

class Filter_cut(djolt_base.Filter):
	_name = "cut"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value, otherwise = "")
		argument = bm_extract.coerce_string(argument, otherwise = "")

		while value and argument:
			x = value.find(argument)
			if x == -1:
				break

			value = value[:x] + value[x + len(argument):]

		return	value

class Filter_default(djolt_base.Filter):
	_name = "default"

	def Filter(self, name, argument, value):
		"""
		If value evaluates to False, use given default. Otherwise, use the value.

		For example:

			{{ value|default:"nothing" }}

		If value is "" (the empty string), the output will be nothing.
		"""

		if value == "":
			return	""

		bvalue = bm_extract.coerce_bool(value, otherwise = False)
		if bvalue:
			return	value
		else:
			return	bm_extract.coerce_string(argument, otherwise = "")

class Filter_otherwise(djolt_base.Filter):
	_name = "otherwise"

	def Filter(self, name, argument, value):
		"""
		Same as default, without the empty string rule
		"""

		bvalue = bm_extract.coerce_bool(value, otherwise = False)
		if bvalue:
			return	value
		else:
			return	bm_extract.coerce_string(argument, otherwise = "")

class Filter_default_if_none(djolt_base.Filter):
	_name = "default_if_none"

	def Filter(self, name, argument, value):
		"""
		If (and only if) value is None, use given default. Otherwise, use the value.
		Note that if an empty string is given, the default value will not be used. 
		Use the default filter if you want to fallback for empty strings.

		For example:

			{{ value|default_if_none:"nothing" }}

		If value is None, the output will be the string "nothing".
		"""

		if value == None:
			return	bm_extract.coerce_string(argument, otherwise = "")
		else:
			return	value

class Filter_divisibleby(djolt_base.Filter):
	_name = "divisibleby"

	def Filter(self, name, argument, value):
		"""
		Returns True if the value is divisible by the argument.

		For example:

			{{ value|divisibleby:"3" }}

		If value is 21, the output would be True.
		"""

		value = bm_extract.coerce_int(value, otherwise = "")
		argument = bm_extract.coerce_int(argument, otherwise = "")

		return	value % argument == 0 and True or False

class Filter_first(djolt_base.Filter):
	_name = "first"

	def Filter(self, name, argument, value):
		"""
		Example:

			{{ value|first }}

		If value is the list ['a', 'b', 'c'], the output will be 'a'.
		"""

		value = bm_extract.coerce_list(value, separator = None)
		if value:
			return	value[0]

class Filter_join(djolt_base.Filter):
	_name = "join"

	def Filter(self, name, argument, value):
		"""
		Joins a list with a string, like Python's str.join(list)

		For example:

			{{ value|join:" // " }}

		If value is the list ['a', 'b', 'c'], the output will be the string "a // b // c".
		"""

		value = bm_extract.coerce_list(value, separator = None)
		value = map(bm_extract.coerce_string, value)
		argument = bm_extract.coerce_string(argument, otherwise = "")

		if value:
			return	argument.join(value)

class Filter_last(djolt_base.Filter):
	_name = "last"

	def Filter(self, name, argument, value):
		"""
		Returns the last item in a list.

		For example:

			{{ value|last }}

		If value is the list ['a', 'b', 'c', 'd'], the output will be the string "d".
		"""

		value = bm_extract.coerce_list(value, separator = None)
		if value:
			return	value[-1]

class Filter_length(djolt_base.Filter):
	_name = "length"

	def Filter(self, name, argument, value):
		try:
			lvalue = len(value)
		except TypeError:
			lvalue = 0

		return	"%d" % lvalue

class Filter_length_is(djolt_base.Filter):
	_name = "length_is"

	def Filter(self, name, argument, value):
		"""
		Returns True if the value's length is the argument, or False otherwise.

		For example:

			{{ value|length_is:"4" }}

		If value is ['a', 'b', 'c', 'd'], the output will be True.
		"""
		try:
			lvalue = len(value)
		except TypeError:
			lvalue = 0

		argument = bm_extract.coerce_int(argument, otherwise = 0)

		return	lvalue == argument

class Filter_linebreaks(djolt_base.Filter):
	_name = "linebreaks"

	def Filter(self, name, argument, value):
		"""
		Replaces line breaks in plain text with appropriate HTML; 
		a single newline becomes an HTML line break (<br />) and a new line followed by a blank line becomes a paragraph break (</p>).

		For example:

			{{ value|linebreaks }}

		If value is Joel\nis a slug, the output will be <p>Joel<br>is a slug</p>.
		"""

Filter_linebreaks()

class Filter_lower(djolt_base.Filter):
	_name = "lower"

	def Filter(self, name, argument, value):
		"""
		Converts a string into all lowercase.

		For example:

			{{ value|lower }}
		"""

		value = bm_extract.coerce_string(value, separator = None)
		if value:
			return	value.lower()

Filter_lower()

class Filter_pluralize(djolt_base.Filter):
	_name = "pluralize"

	def Filter(self, name, argument, value):
		"""
		Returns a plural suffix if the value is not 1. By default, this suffix is 's'.

		Example:

			You have {{ num_messages }} message{{ num_messages|pluralize }}.

		For words that require a suffix other than 's', you can provide an alternate suffix as a parameter to the filter.

		Example:

			You have {{ num_walruses }} walrus{{ num_walrus|pluralize:"es" }}.

		For words that don't pluralize by simple suffix, you can specify both a singular and plural suffix, separated by a comma.

		Example:

			You have {{ num_cherries }} cherr{{ num_cherries|pluralize:"y,ies" }}.
		"""

		ivalue = bm_extract.coerce_int(value)

		plurals = filter(None, bm_extract.coerce_string(argument, otherwise = "").split(",", 1))
		if len(plurals) == 0:
			plurals = [ "", "s" ]
		elif len(plurals) == 1:
			plurals = [ "", plurals[0] ]

		if ivalue == 1:
			return	plurals[0]
		else:
			return	plurals[1]

Filter_pluralize()

class Filter_random(djolt_base.Filter):
	_name = "random"

	def Filter(self, name, argument, value):
		"""
		Returns a random item from the given list.

		For example:

			{{ value|random }}

		If value is the list ['a', 'b', 'c', 'd'], the output could be "b".
		"""

		value = bm_extract.coerce_list(value, separator = None)
		if value:
			return	random.choice(value)

Filter_random()

class Filter_slug(djolt_base.Filter):
	_name = "slug"

	def Filter(self, name, argument, value):
		value = bm_extract.coerce_string(value)
		value = sluggie_rex.sub("-", value)
		value = dash_rex.sub("-", value)
		value = value.strip("-")
		value = value.lower()

		return	value

Filter_slug()

class Filter_upper(djolt_base.Filter):
	_name = "upper"

	def Filter(self, name, argument, value):
		"""\
		Converts a string into all uppercase.

		For example:

			{{ value|upper }}

		If value is "Joel is a slug", the output will be "JOEL IS A SLUG".
		"""
		value = bm_extract.coerce_string(value, separator = None)
		if value:
			return	value.upper()

Filter_upper()

class Filter_title(djolt_base.Filter):
	_name = "title"

	def Filter(self, name, argument, value):
		"""\
		Converts a string into titlecase.

		For example:

			{{ value|title }}

		If value is "Joel is a slug", the output will be "Joel Is A Slug".
		"""
		value = bm_extract.coerce_string(value, separator = None)
		if value:
			return	string.capwords(value)

Filter_title()

class Filter_urlencode(djolt_base.Filter):
	_name = "urlencode"

	def Filter(self, name, argument, value):
		"""\
		URL encodes a string

		For example:

			{{ value|urlencode }}

		If value is "Joel is a/slug", the output will be "Joel%20is%20a%2Fslug".
		"""
		value = bm_extract.coerce_string(value, separator = None)
		if value:
			return	urllib.quote(value, safe = '')

Filter_urlencode()

Filter_add()
Filter_cut()
Filter_default()
Filter_otherwise()
Filter_default_if_none()
Filter_divisibleby()
Filter_first()
Filter_join()
Filter_last()
Filter_length()
Filter_length_is()
