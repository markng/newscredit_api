#
#   bm_date.py
#
#   David Janes
#   2006.06.04
#
#	Everything related to date and time

import os
import re
import sys
import types
import time
import datetime
import calendar

import datetime as python_datetime
import locale as python_locale

from bm_log import Log

try:
	import dateutil.parser
except ImportError:
	dateutil = None

try:
	import pytz
except ImportError:
	pytz = None

offset_tz_re = "^(?P<sign>[-+])(?P<hours>\d\d):?(?P<minutes>\d\d)$"
offset_tz_rex = re.compile(offset_tz_re)

DEVELOPMENT = 1

class DateHelper:
	"""Flexibly break up dates, especially useful for Cheetah templates"""

	def __init__(self, value = None, tz = 'UTC', force_gmt = False):
		"""
		example: "2005-05-04T13:03:40Z", 1166894735.86, 1166894735, <datetime object>

		Parameters:
		- if 'force_gmt' is True, somehow the value is expressed as localtime even
		  though we are expecting GMT. This makes a correction.
		  ONLY works with tuples & ints.
		"""
		self._setup(value, tz, force_gmt)

	def _setup(self, value, tz, force_gmt = False):
		self.tz = tz
		self.tzinfo = None
		if pytz and tz:
			omatch = offset_tz_rex.match(tz)
			if omatch:
				sign = omatch.group('sign').strip('+') + '1'
				hours = omatch.group('hours').lstrip('0') or "0"
				minutes = omatch.group('minutes').lstrip('0').zfill(2)

				try: 
					self.tzinfo = pytz.FixedOffset(int(sign) * ( int(hours) * 60 + int(minutes) ))
					self.tzinfo.dst = lambda x: datetime.timedelta(0)
				except:
					Log("bad TZ -- ignoring", exception = True, tz = tz)
			else:
				try:
					self.tzinfo = pytz.timezone(tz)				
				except:
					Log("bad TZ -- ignoring", exception = True, tz = tz)

		self.time_secs = time.time() # assumed to be UTC
		self.dt = dt_now().fromtimestamp(self.time_secs, self.tzinfo)
		self.tt = self.dt.timetuple()

		if value.__class__ == DateHelper:
			self.time_secs = value.time_secs
			self.dt = value.dt
			self.tt = value.tt
			self.tz = value.tz
			self.tzinfo = value.tzinfo
		elif type(value) in types.StringTypes:
			try:
				v = float(value)
				if v < 21000000:
					raise	ValueError

				self.time_secs = v
				self.dt = dt_now().fromtimestamp(self.time_secs, self.tzinfo)
				self.tt = self.dt.timetuple()
			except:
				done = False
				if dateutil:
					try:
						self.dt = dateutil.parser.parse(value)
						if self.tzinfo:
							if self.dt.tzinfo == None:
								if hasattr(self.tzinfo, 'localize'):
									self.dt = self.tzinfo.localize(self.dt, is_dst = bool(self.dt.timetuple()[-1] == 1))
								else:
									self.dt = self.dt.replace(tzinfo = self.tzinfo)
							else:
								self.dt = self.dt.astimezone(self.tzinfo)

						self.tt = self.dt.timetuple()
						self.time_secs = time.mktime(self.tt)

						done = True
					except:
						Log(exception = True)
						pass

				if not done:
					if value.endswith("Z"):
						value = value[:-1]

					x = None
					temp_tt = None
					for format in [ 
					  "%Y-%m-%dT%H:%M:%S",
					  "%Y%m%dT%H%M%S",
					  "%Y-%m-%dT%H:%M",
					  "%Y%m%dT%H%M",
					  "%Y-%m-%dT%H",
					  "%Y%m%dT%H",
					  "%Y-%m-%d",
					  "%Y%m%d",
					  "%Y-%m",
					  "%Y%m",
					  "%Y",
					  None,
					  ]:
						try:
							if not format:
								raise	x

							#self.tt = time.strptime(value, format)
							temp_tt = time.strptime(value, format)
							if temp_tt:
								self.tt = temp_tt
								self.time_secs = time.mktime(self.tt)
								self.dt = dt_now().fromtimestamp(self.time_secs,self.tzinfo)
								break
						except ValueError, x:
							pass
		elif type(value) in [ types.ListType, types.TupleType, ] and len(value) == 9:
			self.time_secs = time.mktime(value)
			if force_gmt:
				self.time_secs -= time.timezone
			self.dt = dt_now().fromtimestamp(self.time_secs,self.tzinfo)
			self.tt = self.dt.timetuple()
		elif type(value) in [ types.IntType, types.FloatType, ]:
			self.time_secs = float( value )
			if force_gmt:
				self.time_secs -= time.timezone
			self.dt = dt_now().fromtimestamp(self.time_secs,self.tzinfo)
			self.tt = self.dt.timetuple()
		elif isinstance(value, python_datetime.datetime):
			self.tt = value.timetuple()
			self.time_secs = time.mktime(self.tt)
			self.dt = value
			# need to extract tzinfo from datetime or set it to default
			if value.tzinfo:
				self.tzinfo = value.tzinfo
			else:
				self.dt = self.dt.replace( tzinfo = self.tzinfo )
		elif not value:
			pass

		#
		#	expand the time
		#
		for tfmt, name in [
		  ( "Y", "year", ),

		  ( "B", "month_name", ),
		  ( "h", "month_abbr", ),
		  ( "m", "month", ),

		  ( "A", "weekday", ),
		  ( "a", "weekday_abbr", ),
		  ( "d", "day", ),

		  ( "I", "hour", ),
		  ( "I", "hour12", ),
		  ( "H", "hour24", ),
		  ( "p", "ampm", ),

		  ( "M", "minute", ),
		  ( "S", "second", ),

		  ( "z", "tziso", ),
		  ( "Z", "tzname", ),
		]:
			setattr(self, name, self.dt.strftime("%" + tfmt))

		for key in [ "day", "month", "year", "hour", "hour12", "hour24", "minute", "second" ]:
			setattr(self, "n_%s" % key, int(getattr(self, key)))

	def __eq__(self, other):
		return	other and self.tt == other.tt

	def __cmp__(self, other):
		return	cmp(self.dt, other and other.dt)

	def __str__(self):
		return	self.dt.isoformat()
		
##		if self.tzinfo:
##			return	self.dt.strftime('%Y-%m-%dT%H:%M:%S%z')
##		else:
##			return	"%s-%s-%sT%s:%s:%sZ" % ( self.year, self.month, self.day, self.hour24, self.minute, self.second, )

	def __float__(self):
		#return	time.mktime(self.tt)
		return	self.time_secs

	def __int__(self):
		return	int( time.mktime(self.tt) )

	def datetime(self):
		return self.dt
		#return	datetime.datetime(*self.tt[:6])

	def add(self, months = 0, weeks = 0, days = 0, hours = 0, minutes = 0, seconds = 0):
		dt = self.dt + datetime.timedelta(days = days + weeks * 7, hours = hours, minutes = minutes, seconds = seconds)

		if months != 0:
			m = dt.month + months - 1
			try:
				dt = dt.replace(year = dt.year + m // 12, month = m % 12 + 1)
			except ValueError:
				try:
					dt = dt.replace(year = dt.year + m // 12, month = m % 12 + 1, day = 30)
				except ValueError:
					dt = dt.replace(year = dt.year + m // 12, month = m % 12 + 1, day = 28)

		self._setup(dt, self.tz)

	def GetISOTZ(self):
		"""Get the ISO format timezone (-i.e, something like [+-]##:##)"""
		return	self.dt.strftime('%z')

	def timezone(self):
		return self.tzinfo.zone

	def IsDST(self):
		try:
			if self.dt.dst() != datetime.timedelta( 0 ):
				return True
		except:
			pass
		return False

	def dst(self):
		try:
			return self.dt.dst()
		except:
			return datetime.timedelta( 0 )

	def day_changed(self, last):
		if last == None:
			return	True

		return	last.day != self.day or last.month != self.month or last.year != self.year

	def month_changed(self, last):
		if last == None:
			return	True

		return	last.month != self.month or last.year != self.year

	def year_changed(self, last):
		if last == None:
			return	True

		return	last.year != self.year

	def ISODate(self, use_tz = True, utc = False):
		dt = self.dt
		if utc:
			tz = None
			if pytz:
				tz = pytz.UTC
			
			dt = datetime.datetime(tzinfo = tz, *self.dt.utctimetuple()[:6])

		if use_tz:
			return	dt.isoformat()

		if dt.utcoffset() != None:
			return	dt.isoformat()[:-6]
		else:
			return	dt.isoformat()

	def RFC822Date(self):
		return	"%(weekday_abbr)s, %(n_day)02d %(month_abbr)s %(n_year)04d %(n_hour)02d:%(n_minute)02d:%(n_second)02d %(tzname)s" % self.__dict__

	def LocaleDate(self):
		locale = python_locale.getlocale(python_locale.LC_ALL)
		language = locale[0]
		if not language:
			language = "en"
		else:
			language = language[:2].lower()

		if language == "en":
			return	"%(month_name)s %(n_day)s, %(year)s" % self.__dict__
		elif language == "fr":
			return	"%(day)s %(month_name)s %(year)s" % self.__dict__
		else:
			return	"%(year)s-%(month)s-%(day)s" % self.__dict__
		
	def LocaleMonthDay(self):
		locale = python_locale.getlocale(python_locale.LC_ALL)
		language = locale[0]
		if not language:
			language = "en"
		else:
			language = language[:2].lower()

		if language == "en":
			return	"%(month_name)s %(n_day)s" % self.__dict__
		elif language == "fr":
			return	"%(day)s %(month_name)s" % self.__dict__
		else:
			return	"%(month)s-%(day)s" % self.__dict__
		
	def LocaleDateTime(self, seconds = False):
		if seconds:
			return	"%s %s:%s:%s" % ( self.LocaleDate(), self.hour24, self.minute, self.second )
		else:
			return	"%s %s:%s" % ( self.LocaleDate(), self.hour24, self.minute, )

	def AgeInDays(self):
		tz = None
		if pytz:
			tz = pytz.UTC

		dt_self = self.datetime()
		dt_now = datetime.datetime.now(tz = tz)

		return	(dt_now - dt_self).days

	def AgeInMinutes(self):
		tz = None
		if pytz:
			tz = pytz.UTC

		dt_self = self.datetime()
		dt_now = datetime.datetime.now(tz = tz)

		delta = (dt_now - dt_self)
		delta_seconds = delta.days * 24 * 3600 + delta.seconds

		return	delta_seconds // 60

#
#
#
def tzlist(dtnow = None, zones = [ 'US', 'Canada', 'Australia', 'Europe' ]):
	"""Return a list of ( timezone_offset, timezone_name, ) pairs, sorted west to east
	
	The timezone_offset may depend on daylight savings, which
	will be relative to 'dtnow', which defaults to the current time
	"""

	if not pytz:
		return	[ ('+0000', 'UTC'), ]

	if dtnow == None:
		dtnow = datetime.datetime.now()

	zused = {}
	results = []
	rejects = []

	for tz_name in pytz.common_timezones:
		rejected = False

		if zones and tz_name != 'UTC':
			if tz_name.split('/')[0] not in zones:
				rejected = True

		tz = pytz.timezone(tz_name)
		dt = tz.localize(dtnow)
		zname = dt.strftime('%z')
		zvalue = int(zname[0] + zname[1:-1].lstrip("0") + zname[-1])

		if rejected:
			rejects.append(( zvalue, zname, tz_name, ))
		else:
			results.append(( zvalue, zname, tz_name, ))
			zused[zname] = 1

	for zvalue, zname, tz_name in rejects:
		if not zused.get(zname):
			results.append(( zvalue, zname, tz_name, ))
			zused[zname ] = 1

	results.sort()
	results = map(lambda t: t[1:], results)
	return	results
		

#
#	From genhelper.py
#
def dt_now() :
	"""Return right now as a datetime"""

	return datetime.datetime.now()

def dt_today() :
	"""Return the current date, no time, a datetime object"""

	now = datetime.datetime.now()
	return datetime.datetime( now.year, now.month, now.day )

def tt2dt(tt) :
	"""Convert a timetuple into a datetime"""

	return datetime.datetime(tt[:6])

def str2dt( date_string, format, time_zone = None ) :
	"""Convert a string in a given Python dateformat to a datetime"""

	time_struct = time.strptime( date_string, format )
	time_secs = time.mktime( time_struct )
	return datetime.datetime( 2005, 1, 1 ).fromtimestamp( time_secs, time_zone )

def normalize_date(the_date, default = None, format = "%Y-%m-%d", time_zone = None):
	"""Normalize a date as a string, datetime.datetime, datetime.date  for use in billing tuple ( year, month, day )"""
	if isinstance(the_date, types.StringTypes):
		dt = str2dt( the_date, format )
		return ( dt.year, dt.month, dt.day )
	elif isinstance(the_date, datetime.datetime) or isinstance( the_date, datetime.date):
		return ( the_date.year, the_date.month, the_date.day )
	elif isinstance(the_date, datetime.time):
		dt = datetime.datetime( 2005, 1, 1 ).fromtimestamp( time_secs, time_zone )
		return ( dt.year, dt.month, dt.day )
	else:
		return default

def parse_datetime(value):
	import dateutil.parser

	if value.lower().strip() in [ "now", "today", "", ]:
		now = datetime.datetime.now()
		return	now.year, now.month, now.day, now.hour, now.minute, now.second

	try:
		date = dateutil.parser.parse(value)
		return	date.year, date.month, date.day, date.hour, date.minute, date.second
	except:
		return	-1, -1, -1, -1, -1, -1

def parse_date(value):
	import dateutil.parser

	if value.lower().strip() in [ "now", "today", "", ]:
		now = datetime.datetime.now()
		return	now.year, now.month, now.day

	try:
		date = dateutil.parser.parse(value)
		return	date.year, date.month, date.day
	except:
		return	-1, -1, -1

def parse_time(value, accept_all_day = False):
	import dateutil.parser

	value = value.lower().strip()
	if value in [ "now", "today", "", ]:
		now = datetime.datetime.now()
		return	now.hour, now.minute, now.second

	if value in [ "noon", ]:
		return	12, 0, 0

	if value in [ "midnight", ]:
		return	0, 0, 0

	if value in [ "morning", "this morning", ]:
		return	8, 0, 0

	if value in [ "evening", "tonight", "this night", ]:
		return	18, 0, 0

	if accept_all_day and value in [ "all day" ]:
		return	24, 0, 0

	try:
		date = dateutil.parser.parse(value)
		return	date.hour, date.minute, date.second
	except:
		try:
			date = dateutil.parser.parse(value + "pm")
			return	date.hour, date.minute, date.second
		except:
			return	-1, -1, -1

