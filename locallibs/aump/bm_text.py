#
#   bm_text.py
#
#   David Janes
#   2005.04.01
#
#   Helper functions for dealing with text
#

import csv
import sys
import os
import os.path
import urllib
import re
import pprint
import types
import time
import random
import socket
import datetime
import fnmatch
import htmlentitydefs
import sets

def tounicode(u, charsets = None):
	"""Unicode normalizer: convert anything to Unicode without throwing an exception
	
	Note: start unsing this everywhere
	"""

	if type(charsets) in types.StringTypes:
		charsets = [ charsets ]

	if type(u) == types.UnicodeType:
		return	u
	elif type(u) == types.StringType:
		charsets = ( charsets or [] ) + [ 'utf-8', 'latin-1' ]
		attempts = []
		for charset in charsets:
			if not charset:
				continue
			if charset in attempts:
				continue

			attempts.append(charset)

			try:
				return	u.decode(charset)
			except:
				pass

		assert(False)	## everything can be encoded as latin-1 (wrongly, of course)
	elif type(u) == types.NoneType:
		return	""
	else:
		return	unicode(u)

def toutf8(u, charsets = None):
	return	tounicode(u, charsets = charsets).encode('utf-8')

def toascii(u, charsets = None):
	return	tounicode(u, charsets = charsets).encode('ascii', 'replace')

unicode2html_table = {
	ord('&'): u'&amp;',
	ord('>'): u'&gt;',
	ord('<'): u'&lt;',
	ord("'"): u'&#39;',
	ord('"'): u'&quot;',
}

def unicode2html(u, br = False, p = False):
	r = tounicode(u).translate(unicode2html_table).encode("ascii", "xmlcharrefreplace")
	if p:
		r = r.strip()
		r = r.replace("\r\n", "\n")
		r = r.replace("\r", "\n")
		r = re.sub("\n\n+", "</p><p>", r)
		r = r.replace("\n", "<br />")
		if r:
			r = "<p>" + r + "</p>"

		return	r
	elif br:
		r = r.replace("\r\n", "\n")
		r = r.replace("\r", "\n")
		r = r.replace("\n", "<br />")

	return	r

def unicode2entities(u):
	return tounicode(u).encode("ascii", "xmlcharrefreplace")

def unicode2xml(u, cdata_length = 0):
	u = tounicode(u)

	if cdata_length and len(u) >= cdata_length and u.find(']]>') == -1:
		return  "<![CDATA[" + u.encode("ascii", "xmlcharrefreplace") + "]]>"
	else:
		return  u.translate(unicode2html_table).encode("ascii", "xmlcharrefreplace")

#
#	HTML scrubbing -- remove HTML and XML markup from documents
#
killhead_re = """^.*<\s*body[^>]*>"""
killhead_rex = re.compile(killhead_re, re.I|re.MULTILINE|re.DOTALL)

killcomment_re= """<!--.*?-->"""
killcomment_rex = re.compile(killcomment_re, re.I|re.MULTILINE|re.DOTALL)

killoption_re= """<OPTION.*[^<]"""
killoption_rex = re.compile(killoption_re, re.I)

killscript_re= """<\s*script.+?<\s*/\s*script\s*>"""
killscript_rex = re.compile(killscript_re, re.I|re.MULTILINE|re.DOTALL)

killnoscript_re= """<\s*noscript.+?<\s*/\s*noscript\s*>"""
killnoscript_rex = re.compile(killnoscript_re, re.I|re.MULTILINE|re.DOTALL)

killa_re= """<\s*a[\s>]>(.+?)<\s*/\s*a[^>]*>"""
killa_rex = re.compile(killa_re, re.I|re.MULTILINE|re.DOTALL)

entity_re = """&(#)?([a-z0-9]*);"""
entity_rex = re.compile(entity_re, re.I|re.MULTILINE|re.DOTALL)

markup_re = """<[^>]*>"""
markup_rex = re.compile(markup_re, re.I|re.MULTILINE|re.DOTALL)

onattr_re = """
	\s
	on([a-z0-9]*)
	\s*=\s*
	(
		(".*?(?<!\\\\)")
		|
		('.*?(?<!\\\\)')
		|
		([^'"][^\s]*)
	)
"""
onattr_rex = re.compile(onattr_re, re.I|re.MULTILINE|re.DOTALL|re.VERBOSE)

def _handle_entity(match):
	try:
		value = match.group(2)

		if match.group(1):
			if value[:1] == 'x':
				v = int(value[1:], 16)
			else:
				v = int(value)

			if v == 160:
				return  " "
			else:
				return  unichr(v)

		return	unichr(htmlentitydefs.name2codepoint.get(value, ord('?')))
	except:
		Log("entity makes no sense", value = match.group(0), exception = True)
		return	""

SCRUB_HEAD			= 0x01
SCRUB_COMMENTS		= 0x02
SCRUB_OPTIONS		= 0x04
SCRUB_SCRIPTS		= 0x08
SCRUB_FULL_ANCHORS	= 0x10
SCRUB_MARKUP		= 0x20
SCRUB_ENTITY		= 0x40
SCRUB_CLEANUP		= 0x80
SCRUB_SIMPLE_MARKUP = 0x100
SCRUB_ALL = SCRUB_HEAD|SCRUB_COMMENTS|SCRUB_OPTIONS|SCRUB_SCRIPTS|SCRUB_FULL_ANCHORS|SCRUB_MARKUP|SCRUB_ENTITY|SCRUB_CLEANUP
SCRUB_EMAIL = SCRUB_HEAD|SCRUB_COMMENTS|SCRUB_OPTIONS|SCRUB_SCRIPTS|SCRUB_SIMPLE_MARKUP|SCRUB_ENTITY|SCRUB_CLEANUP

def scrub_html(text, scrub = SCRUB_ALL):
	if type(text) == types.UnicodeType:
		pass
	elif type(text) == types.StringType:
		try: text = text.decode('utf-8')
		except:
			text = text.decode('iso-8859-1')
	else:
		text = unicode(text)

	if scrub & SCRUB_ENTITY: text = entity_rex.sub(_handle_entity, text)
	if scrub & SCRUB_COMMENTS: text = killcomment_rex.sub(" ", text)
	if scrub & SCRUB_HEAD and False: text = killhead_rex.sub(" ", text)
	if scrub & SCRUB_SCRIPTS:
		text = killscript_rex.sub(" ", text)
		text = killnoscript_rex.sub(" ", text)
		text = markup_rex.sub(lambda match : onattr_rex.sub("", match.group(0)), text)
	## if scrub & SCRUB_FULL_ANCHORS: text = killa_rex.sub("\\1", text)
	if scrub & SCRUB_OPTIONS: text = killoption_rex.sub(" ", text)
	if scrub & SCRUB_CLEANUP:
		text = " ".join(text.split())
	if scrub & SCRUB_SIMPLE_MARKUP:
		text = re.sub("<\s*/?(span|b|i|strong|em)[^>]*?>", "", text)
	if scrub & SCRUB_MARKUP:
		text = re.sub("<\s*/?(span|b|i|strong|em)[^>]*?>", "", text)
		text = re.sub("<[^>]*?>", "\n", text)
	if scrub & SCRUB_CLEANUP:
		text = text.strip()
		text = re.sub(u"\x93", u" ", text)
		text = re.sub(u"\s*\n\s*", u"\n", text)
		text = re.sub(u"[ \t]+", u" ", text)

	return	text

def safe_parameterd(d):
	"""Make sure the dictionary is safe to pass as a **parameter"""

	ok = True

	for key in d.iterkeys():
		if type(key) != types.StringType:
			ok = False
			break

	if ok:
		return	d

	return	dict(map(lambda kv: ( toascii(kv[0]), kv[1] ), d.iteritems()))
