#
#	webservice.py
#
#	David Janes
#	BlogMatrix
#	2005.12.06
#

import sys
import os
import os.path
import cgi
import cgitb; cgitb.enable()
import pprint
import types
import re
import StringIO
import urllib2
import xml.parsers.expat

try:
	import json
except:
	try:
		import simplejson as json
	except:
		json = None


from optparse import OptionParser

import microformat
microformat.debug = 0

parser = OptionParser()
parser.add_option(
	"", "--fragment",
	action = "store_true",
	default = False,
	dest = "fragment",
	help = "Only return an XHTML fragment")
parser.add_option(
	"", "--header",
	action = "store_true",
	default = False,
	dest = "header",
	help = "Return the HTTP header")
parser.add_option(
	"", "--cgi",
	action = "store_true",
	default = False,
	dest = "cgi",
	help = "Running in a CGI environment")
parser.add_option(
	"", "--static",
	action = "store_true",
	default = False,
	dest = "static",
	help = "Just produce the UI part")
parser.add_option(
	"", "--microformat",
	default = "",
	dest = "microformat",
	help = "The name of the microformat to process")
parser.add_option(
	"", "--format",
	default = "html",
	dest = "format",
	help = "The name of the output format")
parser.add_option(
	"", "--uri",
	default = "",
	dest = "uri",
	help = "URI to read")

(options, args) = parser.parse_args()

if options.cgi:
	params = {}
	for key, value in cgi.parse().iteritems():
		if type(value) == types.ListType:
			if value:
				params[key] = value[0]
		else:
			params[key] = value

	if not params.get("microformat"):
		options.static = True
	else:
		options.microformat = params.get("microformat", "")
		options.format = params.get("format", "html")

		uri = params.get("uri")
		if uri:
			options.uri = uri
		else:
			sys.stdin = StringIO.StringIO(params.get("body", ""))

def footer():
	gtracker = os.environ.get('GOOGLE_ANALYTICS_TRACKER')
	if gtracker:
		print """
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%%3E%%3C/script%%3E"));
</script>
<script type="text/javascript">
var pageTracker = _gat._getTracker("%s");
pageTracker._trackPageview();
</script>
</body>
</html>
""" % gtracker
	else:
		print """</body></html>"""


if options.static:
	if options.header:
		print "Content-Type: text/html"
		print

	print """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
<title>Almost Universal Microformat Parser</title>
<link rel="stylesheet" href="resources/css.css" type="text/css">
</head>
<body>
<h1>
Almost Universal Microformat Parser - Demo
</h1>
<p>
This page will break apart some common microformats
into their component pieces.
</p>
<h2>Visit Us</h2>
<ul>
	<li>
		<a href="http://code.davidjanes.com/#aumfp">Home page</a>
	</li>
	<li>
		<a href="http://code.davidjanes.com/aumfp/demo/">Official demo</a>
	</li>
	<li>
		<a href="http://code.google.com/p/aump/">Source on Google Code</a>
	</li>
</ul>

<h2>
Parse by URI
</h2>

<form method="get" action="">
<table>
	<tr>
		<td width="125">URI</td>
		<td>
			<input type="text" name="uri" value="" size="63" />
		</td>
	</tr>
	<tr>
		<td>Microformat</td>
		<td>
			<select name="microformat">
				<option value="hatom">hAtom</option>
				<option value="hcalendar">hCalendar</option>
				<option value="hcard">hCard</option>
				<option value="hcard-scrubbed">hCard (scrubbed)</option>
				<option value="hlisting">hListing (experimental)</option>
				<option value="hresume">hResume</option>
				<option value="hreview">hReview</option>
				<option value="xfolk">xFolk</option>
				<option value="reltag">rel-tag</option>
			</select>
		</td>
	</tr>
	<tr>
		<td>Output Format</td>
		<td>
			<select name="format">
				<option value="html">HTML</option>
				<option value="json">JSON</option>
			</select>
		</td>
	</tr>
	<tr>
		<td></td>
		<td><button type="submit">Submit</button></td>
	</tr>
</table>
</form>

<h2>
Parse from text
</h2>


<form method="post" action="">
<table>
	<tr>
		<td valign="top" width="125">XHTML fragment</td>
		<td>
			<textarea name="body" rows="12" cols="60"></textarea>
		</td>
	</tr>
	<tr>
		<td>Microformat</td>
		<td>
			<select name="microformat">
				<option value="hatom">hAtom</option>
				<option value="hcalendar">hCalendar</option>
				<option value="hcard">hCard</option>
				<option value="hcard-scrubbed">hCard (scrubbed)</option>
				<option value="hresume">hResume</option>
				<option value="hreview">hReview</option>
				<option value="xfolk">xFolk</option>
				<option value="reltag">rel-tag</option>
			</select>
		</td>
	</tr>
	<tr>
		<td>Output Format</td>
		<td>
			<select name="format">
				<option value="html">HTML</option>
				<option value="json">JSON</option>
			</select>
		</td>
	</tr>
	<tr>
		<td></td>
		<td><button type="submit">Submit</button></td>
	</tr>
</table>
</form>
"""
	footer()
	sys.exit(0)

if not options.microformat:
	if options.header:
		print "Status: 400"
		print "Content-Type: text/plain"
		print

	print "400 - missing microformat"
	sys.exit(0)

parser = None

if options.microformat == "hatom":
	import hatom
	parser = hatom.MicroformatHAtom(page_uri = options.uri)
elif options.microformat == "hresume":
	import hresume
	parser = hresume.MicroformatHResume(page_uri = options.uri)
elif options.microformat == "hlisting":
	import hlisting
	parser = hlisting.MicroformatHListing(page_uri = options.uri)
elif options.microformat == "hreview":
	import hreview
	parser = hreview.MicroformatHReview(page_uri = options.uri)
elif options.microformat in [ "hcard", "hcard-scrubbed", ]:
	import hcard
	import uf_vcard
	parser = hcard.MicroformatHCard(page_uri = options.uri)
elif options.microformat == "hcalendar":
	import hcalendar
	parser = hcalendar.MicroformatHCalendar(page_uri = options.uri)
elif options.microformat == "xfolk":
	import xfolk
	parser = xfolk.MicroformatXFolk(page_uri = options.uri)
elif options.microformat == "reltag":
	import reltag
	parser = reltag.MicroformatRelTag(page_uri = options.uri)
else:
	if options.header:
		print "Status: 400"
		print "Content-Type: text/plain"
		print

	print "400 - unknown microformat '%s'" % options.microformat
	sys.exit(0)

def _(value):
	if type(value) in types.StringTypes:
		value = value.encode('ascii', 'xmlcharrefreplace')
		if value.find(' ') == -1 and ( value.startswith("http://") or value.startswith("https://") ):
			if value.endswith(".jpg") or value.endswith(".png") or value.endswith(".gif"):
				return	"<a href='%s'>%s</a><br /><img src='%s' alt='photo' />" % ( value, value, value, )
			else:
				return	"<a href='%s'>%s</a>" % ( value, value, )
		else:
			return	value
	else:
		return	""

def print_record(parsed):
	if not parsed:
		pass
	elif isinstance(parsed, dict):
		print_record_dict(parsed)
	elif isinstance(parsed, list):
		print_record_dict(list)
	else:
		print _(parsed)

def print_record_list(parsed):
	print "<ul>"
	for item in parsed:
		print "<li>"
		print_record(item)
		print "</li>"
	print "</ul>"

def print_record_dict(parsed):
	#
	#	Normal data
	#
	keys = parsed.keys()
	keys.sort()
	keys = filter(lambda k: type(parsed[k]) != types.ListType, keys)

	print "  <dl>"
	for key in keys:
		if key == '@html':
			continue

		value = parsed[key]
		if not value:
			continue

		print "   <dt>%s</dt>" % key

		if type(value) in types.StringTypes:
			print "   <dd>%s</dd>" % _(value)

	print " </dl>"

	#
	#	Structured
	#
	keys = parsed.keys()
	keys.sort()
	keys = filter(lambda k: type(parsed[k]) == types.ListType, keys)

	for key in keys:
		print " <dt>%s</dt>" % key
		print " <dd><ol>"

		for map in parsed[key]:
			print "  <li>"
			print_record(map)

		print " </ol></dd>"


if options.format == 'html':
	if options.header:
		print "Content-Type: text/html; charset=utf-8"
		print

	if not options.fragment:
		print """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
		"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
<title>Microformat Details</title>
<link rel="stylesheet" href="resources/css.css" type="text/css">
<style type="text/css">
#id_results li {
	border: 1px dashed #FF9;
	background-color: #FFE;
	padding: 5px;
	margin-bottom: 5px;
    list-style: none !important;
    margin-left: 0px !important;
	margin-bottom: 5px !important;
}
#id_results ol li {
	border: 1px dashed #FFE;
	margin-bottom: 0px;
    list-style: none !important;
}
body {
	width: 800px;
}
#id_results dd {
	border: 1px dashed #CCC;
	background-color: #EEE;
	padding: 5px;
}
div#id_results {
	margin-top: 25px;
}
</style>
</head>
<body>
<h1>Almost Universal Microformat Parser - Parsing Results</h1>
"""

	fins = []
	errors = []
	if options.uri:
		fins = [ options.uri ]
	elif options.cgi and params.get('body') != None:
		fins = [ StringIO.StringIO(params['body']), ]
	elif args:
		fins = map(lambda f: open(f, 'rb'), args)
	else:
		fins = [ sys.stdin, ]

	print "<ul>"
	print "<li><a href='?'>Try another</a></li>"
	if options.uri:
		print "<li>page: <a href='%s'>%s</a></li>" % ( options.uri, options.uri, )
	print "</ul>"
	print "<div id='id_results'>"

	for fin in fins:
		if type(fin) not in types.StringTypes:
			try:
				x = fin.read().strip()
				parser.Feed(x)
			except xml.parsers.expat.ExpatError, x:
				if hasattr(fin, "name"):
					errors.append((fin.name, str(x)))
				else:
					errors.append(('<stdin>', str(x)))

				continue

		list_re = "^(?P<count>\d\d+)-(?P<tag>[^.]+)(?P<remainder>.*)$"
		list_rex = re.compile(list_re)

		mf_count = -1
		for parsed in parser.Iterate():
			mf_count += 1

			if options.microformat in [ "hcard-scrubbed", ]:
				uf_vcard.scrub(parsed)

			print "<h2>%s: %s</h2>" % (
				parsed.get('@uf', '[No uF]'),
				_(parsed.get('@title', '[No Title]')),
			)

			at_index = parsed.get('@index')
			if at_index:
				print " <div id='%s'>" % ( at_index, )
			else:
				print " <div>"

			if type(fin) in types.StringTypes:
				parsed['@uri'] = fin
			elif hasattr(fin, "name"):
				if fin.name.startswith("http://"):
					parsed['@uri'] = fin.name
				else:
					parsed['@file'] = fin.name

			print_record(parsed)
			print "</div>"

	if errors:
		for ( src, error, ) in errors:
			print "<p>%s<br/>%s</p>" % ( cgi.escape(src), cgi.escape(error), )

	print "</div>"
	if not options.fragment:
		print """\
	<p>
	<a href="http://validator.w3.org/check?uri=referer"><img
			border="0"
			src="http://www.w3.org/Icons/valid-xhtml10"
			alt="Valid XHTML 1.0!" height="31" width="88" /></a>
	</p>
	"""
	footer()
elif options.format == 'json':
	if not json:
		print "Content-Type: text/plain; charset=utf-8"
		print
		print "JSON is not installed on this machine -- contact an admin"
		sys.exit(0)

	if options.header:
		print "Content-Type: text/javascript; charset=utf-8"
		print

	fins = []
	errors = []
	if options.uri:
		fins = [ options.uri ]
	elif args:
		fins = map(lambda f: open(f, 'rb'), args)
	else:
		fins = [ sys.stdin, ]

	results = []
	for fin in fins:
		if type(fin) not in types.StringTypes:
			try:
				parser.Feed(fin.read())
			except xml.parsers.expat.ExpatError, x:
				if hasattr(fin, "name"):
					errors.append((fin.name, str(x)))
				else:
					errors.append(('<stdin>', str(x)))

				continue

		mf_count = -1
		for parsed in parser.Iterate():
			mf_count += 1

			if type(fin) in types.StringTypes:
				parsed['@uri'] = fin
			elif hasattr(fin, "name"):
				if fin.name.startswith("http://"):
					parsed['@uri'] = fin.name
				else:
					parsed['@file'] = fin.name

			results.append(parsed)

	json.dump(results, sys.stdout)
