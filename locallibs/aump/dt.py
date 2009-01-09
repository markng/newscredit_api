#
#	dt.py
#
#	David Janes
#	BlogMatrix
#	2005.12.05
#

import sys
import re

dt_re = """

	^

	(?P<year>\d\d\d\d)
	(
		([/-])?(?P<month>\d\d)
		(
			([/-])?(?P<day>\d\d)
		)?
	)?
	(
		(T|\s+)
		(?P<hour>\d\d)
		(
			([:])?(?P<minute>\d\d)
			(
				([:])?(?P<second>\d\d)
				(
					([.])?(?P<fraction>\d+)
				)?
			)?
		)?
	)?
	(
		(?P<tzzulu>Z)
		|
		(?P<tzoffset>[-+])
		(?P<tzhour>\d\d)
		([:])?(?P<tzminute>\d\d)
	)?
"""

dt_rex = re.compile(dt_re, re.VERBOSE)

def normalize(dtstr):
	match = dt_rex.match(dtstr)
	if not match:
		return	""

	if match.group("day"):
		result = "%s-%s-%s" % ( match.group("year"), match.group("month"), match.group("day"), )
	elif match.group("month"):
		result = "%s-%s" % ( match.group("year"), match.group("month"), )
	else:
		result = "%s" % ( match.group("year"), )

	if match.group("hour"):
		result += "T%s" % match.group("hour")
		if match.group("minute"):
			result += ":%s" % match.group("minute")
			if match.group("second"):
				result += ":%s" % match.group("second")

	if match.group("tzzulu"):
		result += "Z";
	else:
		tzoffset = match.group("tzoffset")
		tzhour = match.group("tzhour")
		tzminute = match.group("tzminute")

		if tzoffset and tzhour and tzminute:
			if tzhour == "00" and tzminute == "00":
				result += "Z"
			else:
				result += "%s%s:%s" % ( tzoffset, tzhour, tzminute, )

	return	result

if __name__ == '__main__':
	tests = [
		"20010203T10:11:12.34Z",
		"2001-02-03T10:11:12.34Z",
		"2001-02-03 10:11:12.34Z",
		"20010203T10:11:12.34-0400",
		"2001-02-03T10:11:12.34-0400",
		"2001-02-03 10:11:12.34-0400",
		"20010203T10:11:12.34+0400",
		"2001-02-03T10:11:12.34+0400",
		"2001-02-03 10:11:12.34+0400",
		"20010203T10:11:12.34-04:00",
		"2001-02-03T10:11:12.34-04:00",
		"2001-02-03 10:11:12.34-04:00",
		"20010203T10:11:12.34+04:00",
		"2001-02-03T10:11:12.34+04:00",
		"2001-02-03 10:11:12.34+04:00",

		"20010203",
		"2001-02-03",
		"20010203T10",
		"2001-02-03T10",
		"20010203T1011",
		"2001-02-03T10:11",
		"20010203T101112",
		"2001-02-03T10:11:12",
		"20010203T101112.34",
		"2001-02-03T10:11:12.34",

		"20010203Z",
		"2001-02-03Z",
		"20010203T10Z",
		"2001-02-03T10Z",
		"20010203T1011Z",
		"2001-02-03T10:11Z",
		"20010203T101112Z",
		"2001-02-03T10:11:12Z",
		"20010203T101112.34Z",
		"2001-02-03T10:11:12.34Z",
	]

	if len(sys.argv) > 1:
		tests = sys.argv[1:]

	for test in tests:
		match = dt_rex.match(test)
		if not match:
			print "no match:", test
		else:
			print "match:", test
			print "normalize", normalize(test)
			for n in [ "year","month","day","hour","minute","second","fraction","tzzulu","tzoffset","tzhour","tzminute",]:
				print n, match.group(n)

		print
