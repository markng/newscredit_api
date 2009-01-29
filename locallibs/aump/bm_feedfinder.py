"""Ultra-liberal RSS feed locator

MODIFIED for pybm

http://diveintomark.org/projects/rss_finder/

Usage:
getFeeds(uri) - returns list of RSS feeds associated with this address

Example:
>>> import rssfinder
>>> rssfinder.getFeeds('http://diveintomark.org/')
['http://diveintomark.org/xml/rss.xml']
>>> rssfinder.getFeeds('macnn.com')
['http://www.macnn.com/macnn.rdf']

Can also use from the command line.  Feeds are returned one per line:
$ python rssfinder.py diveintomark.org
http://diveintomark.org/xml/rss.xml

How it works:
0. At every step, RSS feeds are minimally verified to make sure they are
   really RSS feeds.
1. If the URI points to an RSS feed, it is simply returned; otherwise
   the page is downloaded and the real fun begins.
2. Feeds pointed to by LINK tags in the header of the page (RSS autodiscovery)
3. <A> links to feeds on the same server ending in ".rss", ".rdf", or ".xml"
4. <A> links to feeds on the same server containing "rss", "rdf", or "xml"
5. <A> links to feeds on external servers ending in ".rss", ".rdf", or ".xml"
6. <A> links to feeds on external servers containing "rss", "rdf", or "xml"
7. As a last ditch effort, we search Syndic8 for feeds matching the URI

DPJ 2004.05.11:
http://nenhures.blogspot.com/2004_05_01_nenhures_archive.html
<link rel="service.feed" type="application/atom+xml" title="nenhures" href="atom.xml" />


"""

__version__ = "1.1"
__date__ = "2003/02/20"
__author__ = "Mark Pilgrim (f8dy@diveintomark.org)"
__copyright__ = "Copyright 2002, Mark Pilgrim"
__license__ = "GPL"
__credits__ = """Abe Fettig for a patch to sort Syndic8 feeds by popularity
Also Jason Diamond, Brian Lalor for bug reporting and patches"""
__history__ = """
1.1 - MAP - 2003/02/20 - added support for Robot Exclusion Standard.  Will
fetch /robots.txt once per domain and verify that URLs are allowed to be
downloaded.  Identifies itself as
  rssfinder/<version> Python-urllib/<version> +http://diveintomark.org/projects/rss_finder/
"""

import types
import bm_uri
import bm_text

from bm_log import Log

_debug = 0
try:
	import xmlrpclib # http://www.pythonware.com/products/xmlrpc/
except ImportError:
	pass
from sgmllib import SGMLParser
import urllib, urlparse, re, sys, urllib2
import os.path
import robotparser
import traceback

class RobotFileParserFixed(robotparser.RobotFileParser):
	"""patched version of RobotFileParser, integrating fixes from Python 2.3a2 and bug 690214"""

	def can_fetch(self, useragent, url):
		"""using the parsed robots.txt decide if useragent can fetch url"""
		if self.disallow_all:
			return 0
		if self.allow_all:
			return 1
		# search for given user agent matches
		# the first match counts
		url = urllib.quote(urlparse.urlparse(urllib.unquote(url))[2]) or "/"
		for entry in self.entries:
			if entry.applies_to(useragent):
				if not entry.allowance(url):
					return 0
		# agent not found ==> access granted
		return 1


import re

anchor_1_re = """<a[^>]*href\s*=\s*"([^">]*)"[^>]*>"""
anchor_1_rex = re.compile(anchor_1_re, re.I|re.MULTILINE|re.DOTALL)
anchor_2_re = """<a[^>]*href\s*=\s*'([^'>]*)'[^>]*>"""
anchor_2_rex = re.compile(anchor_2_re, re.I|re.MULTILINE|re.DOTALL)
anchor_3_re = """<a[^>]*href\s*=\s*([^\s>]*)[^>]*>"""
anchor_3_rex = re.compile(anchor_3_re, re.I|re.MULTILINE|re.DOTALL)

link_1_re = """<link[^>]*>"""
link_1_rex = re.compile(link_1_re, re.I|re.MULTILINE|re.DOTALL)

all_re = "(" + "|".join([anchor_1_re, anchor_2_re, anchor_3_re, link_1_re, ]) + ")"
all_rex = re.compile(all_re, re.I|re.MULTILINE|re.DOTALL)

link_tags_1_re = """(type|href|rel)\s*=\s*"([^">]*)"""
link_tags_1_rex = re.compile(link_tags_1_re, re.I|re.MULTILINE|re.DOTALL)
link_tags_2_re = """(type|href|rel)\s*=\s*'([^'>]*)"""
link_tags_2_rex = re.compile(link_tags_2_re, re.I|re.MULTILINE|re.DOTALL)
link_tags_3_re = """(type|href|rel)\s*=\s*([^\s>]*)"""
link_tags_3_rex = re.compile(link_tags_3_re, re.I|re.MULTILINE|re.DOTALL)

all_link_tags_re = "(" + "|".join([link_tags_1_re, link_tags_2_re, link_tags_3_re, ]) + ")"
all_link_tags_rex = re.compile(all_link_tags_re, re.I|re.MULTILINE|re.DOTALL)

types_syndication = [
	"text/rdf+xml", "text/rdf", "text/rss", "text/rss+xml",
	"application/rdf+xml", "application/rdf", "application/rss", "application/rss+xml",
	"application/x.atom+xml", "application/atom+xml",
]

types_maybe = [
	"text/plain",
	"text/xml",
	"application/xml",
] + types_syndication

class BaseParser(SGMLParser):
	def __init__(self, baseuri):
		SGMLParser.__init__(self)
		self.links = []
		self.baseuri = baseuri
		self.startlink = None
		self.homelink = None
		self.prearchiveslink = None

	def feed(self, data):
		try:
			SGMLParser.feed(self, data)
			return
		except:
			if _debug: traceback.print_exc(file = sys.stderr, limit = 2)

		Log('using alternate re-based parser', verbose = True)

		for match in all_rex.finditer(data):
			text = match.group(0)

			if hasattr(self, "start_a"):
				match = anchor_1_rex.match(text)
				if not match: match  = anchor_2_rex.match(text)
				if not match: match  = anchor_3_rex.match(text)
				if match:
					attrs = [ ( "href", match.group(1)) ]
					self.start_a(attrs)
					continue

			if hasattr(self, "do_link"):
				match = link_1_rex.match(text)
				if match:
					attrs = []
					for tvmatch in all_link_tags_rex.finditer(text):
						tvtext = tvmatch.group(0)

						tvmatch = link_tags_1_rex.match(tvtext)
						if not tvmatch: tvmatch = link_tags_2_rex.match(tvtext)
						if not tvmatch: tvmatch = link_tags_3_rex.match(tvtext)
						if tvmatch:
							attrs.append(( tvmatch.group(1), tvmatch.group(2) ))

					# print text, attrs
					self.do_link(attrs)
					continue

class LinkParser(BaseParser):
	def do_link(self, attrs):
		rels = [v for k,v in attrs if k=='rel']
		if not rels: return

		rel = rels[0]
		if rel == "start":
			hrefs = [v for k,v in attrs if k=='href']
			if hrefs: self.startlink = urlparse.urljoin(self.baseuri, hrefs[0])
		elif rel == "home":
			hrefs = [v for k,v in attrs if k=='href']
			if hrefs: self.homelink = urlparse.urljoin(self.baseuri, hrefs[0])
		elif rel in [ "service.feed", "alternate" ]:
			types = [v for k,v in attrs if k=='type']
			if not types: return
			type = types[0]
			isRSSType = 0
			for t in types_syndication:
				isRSSType = type.startswith(t)
				if isRSSType: break
			if not isRSSType: return
			hrefs = [v for k,v in attrs if k=='href']
			if not hrefs: return

			uri = hrefs[0]
			try: uri = bm_text.html2unicode(uri)
			except: pass

			self.links.append(urlparse.urljoin(self.baseuri, uri))

class ALinkParser(BaseParser):
	def start_a(self, attrs):
		hrefs = [v for k,v in attrs if k=='href']
		if not hrefs: return
		self.links.append(urlparse.urljoin(self.baseuri, hrefs[0]))

def makeFullURI(uri):
	if uri.find(':') == -1:
		uri = 'http://%s' % uri

	return uri

def getLinks(data, baseuri):
	p = LinkParser(baseuri)
	p.feed(data)
	return scrubLinks(p.links)

def getALinks(data, baseuri):
	p = ALinkParser(baseuri)
	p.feed(data)
	return scrubLinks(p.links)

def getLocalLinks(links, baseuri):
	baseuri = baseuri.lower()
	urilen = len(baseuri)
	return scrubLinks([l for l in links if l.lower().startswith(baseuri) or l.find("blogmatrix") > -1])

def scrubLinks(links):
	nlinks = []
	for link in links:
		hashx = link.find("#")
		if hashx > -1:
			link = link[:hashx]

		if link not in nlinks:
			nlinks.append(link)

	return	nlinks

def isFeedBurnerLink(link):
	return link.startswith("http://feeds.feedburner.com/")

def isFeedLink(link):
	return link[-4:].lower() in ('.rss', '.rdf', '.xml', '.atom' )

def isXMLRelatedLink(link):
	if link.endswith("/"):
		return	False

	#
	#	All this nonsense is because of http://codespeak.net/lxml/,
	#	which creates huge numbers of false positives
	#
	link = os.path.basename(link).lower()
	x, ext = os.path.splitext(link)
	if ext in [ ".gif", ".png", ".jpg", ".jpeg", ".html", ".htm", ".shtml", ".gz", ".tgz", ".zip", ".Z", ".txt", ".pdf", ".doc", ".docx", ".swf", ".xls", ".xlsx", ".ppt", ".pptx", ]:
		return	False

	return link.count('rss') + link.count('rdf') + link.count('xml')

def isRSS(data):
	data = data[:2024].lower()
	if data.count('<html'): return 0
	return data.count('<rss') + data.count('<rdf') + data.count('<feed')

def isOPML(data):
	data = data.lower()
	if data.count('<html'): return 0
	return data.count('<opml')

def sortFeeds(feed1Info, feed2Info):
	return cmp(feed2Info['headlines_rank'], feed1Info['headlines_rank'])

class RSSFinder:
	def __init__(self, uri, ignore_robots = 0, follow_start = 1, skip_syndic8 = False, hints = None):
		self.uri = uri
		self.fulluri = os.path.isfile(uri) and uri or makeFullURI(uri)
		self.ignore_robots = ignore_robots
		self.follow_start = follow_start	# follow <link rel='start'> first
		self.skip_syndic8 = skip_syndic8
		self.contents = None
		self.ctype = None
		self.current_ctype = None
		self.auth_prompt = None

		if type(hints) in types.StringTypes:
			self.hints = [ hints ]
		elif type(hints) == types.ListType:
			self.hints = hints
		else:
			self.hints = []

		self.seen_uris = {}

		#
		# results
		#
		self.feeds = []
		self.htmluri = None

		#
		# old gatekeeper code
		#
		self.rpcache = {} # a dictionary of RobotFileParserFixed objects, by domain
#		self.urlopener = urllib.FancyURLopener()
#		self.urlopener.version = "rssfinder/" + __version__ + " " + self.urlopener.version + " +http://diveintomark.org/projects/rss_finder/"
#		Log(self.urlopener.version, verbose = True)
#		self.urlopener.addheaders = [('User-agent', self.urlopener.version)]
#		robotparser.URLopener.version = self.urlopener.version
#		robotparser.URLopener.addheaders = self.urlopener.addheaders

	def findFeeds(self):
		#
		#	getData always returns the redirects, to get the real
		#	url location. XXX -- make sure we're not returning
		#	temporary URLs
		#
		self.contents, real_uri = self.getData(self.fulluri, allow_files = True)
		self.ctype = self.current_ctype

		# is this already a feed?
		if isRSS(self.contents):
			self.feeds = [self.fulluri]
			return

		# we don't touch OPML
		if isOPML(self.contents):
			return	[]

		# nope, it's a page, try LINK tags first
		Log('looking for LINK tags', verbose = True)
		self.htmluri = real_uri

		#
		#	check the HTML link given
		#
		self.feeds, startlink = self.getFeedsFromContents(self.fulluri, self.contents)

		#
		#	if there is a <link rel='start'> and 'follow_start' is set,
		#	use that to determine where the feeds are. This fact will
		#	be recorded by 'self.htmluri' being non-None
		#
		if self.follow_start and startlink:
			Log('using "start" link "%s"' % startlink, verbose = True)
			data, real_uri = self.getData(startlink)

			feeds, ignore_this_startlink = self.getFeedsFromContents(startlink, data)
			if feeds:
				self.feeds = feeds
				self.htmluri = real_uri
				self.fulluri = real_uri
				self.contents = data

		Log('found %s self.feeds through LINK tags' % len(self.feeds), verbose = True)
		self.feeds = filter(self.isFeedAny, self.feeds)
		if self.feeds: return

		#
		# no LINK tags, look for regular <A> links that point to self.feeds
		#
		Log('no LINK tags, looking at A tags', verbose = True)
		links = getALinks(self.contents, self.fulluri)
		locallinks = getLocalLinks(links, self.fulluri)

		if self.hints:
			Log('checking hints: %s' % self.hints, verbose = True)
			print links
			for hint_re in self.hints:
				hint_rex = re.compile(hint_re, re.I)

				for link in locallinks:
					if hint_rex.search(link):
						self.feeds.append(link)
				
			if self.feeds: return

			for hint_re in self.hints:
				hint_rex = re.compile(hint_re, re.I)

				for link in links:
					if hint_rex.search(link):
						self.feeds.append(link)
				
			if self.feeds: return

		# look for obvious feed links on the same server
		## Log("HERE:A")
		self.feeds = self.confirming_filter(self.isFeed, filter(isFeedBurnerLink, links), "feedburner - obvious")
		if self.feeds: return

		## Log("HERE:B")
		# look for obvious feed links on the same server
		self.feeds = self.confirming_filter(self.isFeed, filter(isFeedLink, locallinks), "same server - obvious")
		if self.feeds: return

		## Log("HERE:C", locallinks = locallinks)
		# look harder for feed links on the same server
		self.feeds = self.confirming_filter(self.isFeed, filter(isXMLRelatedLink, locallinks), "same server - harder")
		if self.feeds: return

		## Log("HERE:D")
		# look for obvious feed links on another server
		self.feeds = self.confirming_filter(self.isFeed, filter(isFeedLink, links), "other servers - obvious")
		if self.feeds: return

		## Log("HERE:E")
		# look harder for feed links on another server - DPJ 2009.01.23: too much garbage
		# self.feeds = self.confirming_filter(self.isFeed, filter(isXMLRelatedLink, links), "other servers - harder")
		# if self.feeds: return

		Log('checked everything without finding any feeds', verbose = True)

	def _getrp(self, url):
		#
		#	it's just too much trouble to integrate with GenericURL
		#	- dpj 2004.11.12
		#
		return

		if not self.ignore_robots:
			protocol, domain = urlparse.urlparse(url)[:2]
			if self.rpcache.has_key(domain):
				return self.rpcache[domain]
			baseurl = '%s://%s' % (protocol, domain)
			robotsurl = urlparse.urljoin(baseurl, 'robots.txt')
			Log('fetching %s' % robotsurl, verbose = True)
			rp = RobotFileParserFixed(robotsurl)
			rp.read()
			self.rpcache[domain] = rp
			return rp

	def can_fetch(self, url):
		if self.ignore_robots:
			return	True

		rp = self._getrp(url)
		if not rp:
			return	True

		allow = rp.can_fetch(self.urlopener.version, url)
		Log("Gatekeeper examined %s and said allow=%s" % (url, allow), verbose = True)
		return allow

	def confirming_filter(self, function, uris, message):
		self.event("examining %d uris (%s)" % (len(uris), message))
		return	filter(function, uris)

	def getData(self, url, xml_only = False, allow_files = False):
		if not self.can_fetch(url): return ''

		try:
			if allow_files and os.path.isfile(url):
				fin = open(url, 'rb')
				data = fin.read()

				return	data, url

			#
			#	Changed to bm_uri
			#	- dpj 2007.11.02
			#
			#	This version uses GenericURL and thus has access to all the
			#	goodies over there (proxy, auth-login)
			#	- dpj 2004.11.12
			#

			self.event("downloading '%s'" % url)

			try:
				uri_downloader = bm_uri.URILoader(uri = url)
				uri_downloader.Load()
			except:
				if _debug: Log(exception = True, uri = uro)
				return	"", url

			if xml_only:
				if self.current_ctype not in types_maybe:
					self.event("ignoring '%s' (content-type is '%s')" % ( url, self.current_ctype ))
					return	"", url

			self.current_ctype = uri_downloader.GetContentType("application/octet-data")

			location = url

			slashx = self.current_ctype.find('/')
			if slashx > -1 and self.current_ctype not in [ "application/xml", "application/rss+xml", "application/xml+rss" ]:
				if self.current_ctype[:slashx] in [ "audio", "video", ]:
					self.event("ignoring '%s' (content-type is '%s')" % ( url, self.current_ctype ))
					return	"", url
			#
			#
			#
			if self.current_ctype in [ "text/html", "text/html" ] and not isRSS(uri_downloader.GetRaw()):
				try:
					html_downloader = bm_uri.URILoader(uri = url)
					html_downloader.Load(raw = uri_downloader.GetRaw())
				except:
					if _debug: Log(exception = True, uri = uro)
					return	"", url

				cooked = html_downloader.GetCooked()
				if not cooked:
					cooked = uri_downloader.GetRaw()

				return	cooked, url
			else:
				return	uri_downloader.GetRaw(), url

		except:
			traceback.print_exc(file = sys.stderr)
			self.event("error downloading '%s'" % url)
			return	"", url

	def isFeedAny(self, uri):
		return	self.isFeed(uri, xml_only = False)

	def isFeed(self, uri, xml_only = True):
		if self.seen_uris.get(uri):
			return	False

		self.seen_uris[uri] = True

		if uri.endswith(".htm") or uri.endswith(".html") or uri.endswith(".shtml"):
			return	False

		Log('verifying that %s is a feed' % uri, verbose = True)
		protocol = urlparse.urlparse(uri)
		if protocol[0] not in ('http', 'https'): return 0
		data, location = self.getData(uri, xml_only = xml_only)
		return isRSS(data)

	def getFeedsFromContents(self, uri_used, data):
		try:
			lp = LinkParser(uri_used)
			lp.feed(data)
			return	lp.links, lp.startlink or lp.homelink or self.guessHomeLink(uri_used)
		except:
			Log("unexpected exception ... ignoring", verbose = True, exception = True, uri = uri_used)

		return	[], None

	def guessHomeLink(self, uri):
		urip = urlparse.urlparse(uri)
		if not urip.path.strip('/'):
			return	None

		parts = filter(None, urip.path.split("/"))
		for index, part in enumerate(parts):
			Log(index = index, part = part)
			if part.startswith("~"):
				return	"%s://%s/%s" % ( urip.scheme, urip.netloc, "/".join(parts[:index + 1]))
			elif part == "archives":
				return	"%s://%s/%s" % ( urip.scheme, urip.netloc, "/".join(parts[:index]))

	def event(self, message):
		pass

if __name__ == '__main__':
	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--debug",
		default = False,
		action = "store_true",
		dest = "debug",
		help = "",
	)
	parser.add_option(
		"", "--uri",
		dest = "uri",
	)
	parser.add_option(
		"", "--hint",
		dest = "hint",
	)

	(options, args) = parser.parse_args()

	class OptionException(Exception):
		pass

	try:
		if not options.uri:
			raise	OptionException, "need --uri=URI"

		if options.debug:
			_debug = 1
			Log.verbose = True

		rssfinder = RSSFinder(options.uri, ignore_robots = True, follow_start = True, hints = options.hint)
		rssfinder.findFeeds()
		
		if options.debug:
			Log(
				feeds = rssfinder.feeds,
				start = rssfinder.htmluri,
			)

		for feed in rssfinder.feeds:
			print feed
	except SystemExit:
		raise
	except OptionException, s:
		print >> sys.stderr, "%s: %s\n" % ( sys.argv[0], s, )
		parser.print_help(sys.stderr)
		sys.exit(1)
	except Exception, x:
		print >> sys.stderr, type(x)

		Log(exception = True)
		parser.print_help(sys.stderr)
		sys.exit(1)
