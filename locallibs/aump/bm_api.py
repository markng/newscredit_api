#
#   bm_api.py
#
#   David Janes
#   2009.01.17
#
#	Copyright 2008, 2009 David Janes
#

import os
import sys
import urllib
import types
import pprint
import types
import sets

try:
	import json
except:
	import simplejson as json

import bm_extract
import bm_uri
import bm_work
import bm_text
import bm_cfg

import djolt

from bm_log import Log

import xml.etree.ElementTree as ElementTree

atom_like = None

namespaced = {
	"access" : "http://www.bloglines.com/about/specs/fac-1.0",
	"atom" : "http://www.w3.org/2005/Atom",
	"blogchannel " : "http://backend.userland.com/blogChannelModule",
	"cf " : "http://www.microsoft.com/schemas/rss/core/2005 " ,
	"content" : "http://purl.org/rss/1.0/modules/content/",
	"creativecommons " : "http://backend.userland.com/creativeCommonsRSSModule",
	"dc" : "http://dublincore.org/documents/dcmi-namespace/",
	"feedburner" : "http://rssnamespace.org/feedburner/ext/1.0",
	"ffa" : "http://www.feedforall.com/ffa-dtd/ ",
	"g" : "http://base.google.com/ns/1.0",
	"geo" : "http://www.w3.org/2003/01/geo/wgs84_pos#",
	"georss" : "http://www.georss.org/georss",
	"itunes" : "http://www.itunes.com/dtds/podcast-1.0.dtd" ,
	"media" : "http://search.yahoo.com/mrss",
	"opensearch" : "http://a9.com/-/spec/opensearchrss/1.0/",
	"product" : "http://www.buy.com/rss/module/product/" ,
	"ra" : "http://www.feedshow.com/xmlrss/remoteads/" ,
	"sx" : "http://www.microsoft.com/schemas/sse",
	"sy" : "http://purl.org/rss/1.0/modules/syndication/",
	"trackback" : "http://madskills.com/public/xml/rss/module/trackback/",
	"wfw" : "http://wellformedweb.org/CommentAPI/",
	"rss" : "http://backend.userland.com/rss2",
	"postrank" : "http://www.postrank.com/xsd/2007-11-30/postrank-2007-11-30.xsd",
	"slash" : "http://purl.org/rss/1.0/modules/slash/",

	#
	#	Non-standard below
	#
	"gsearch" : "http://code.google.com/apis/ajaxsearch/",
	"email" : "http://www.ietf.org/rfc/rfc2822.txt",
	"hcard" : "http://purl.org/uF/hCard/1.0/",
	"haudio" : "http://purl.org/NET/haudio",
	"hatom" : "http://purl.org/uF/hAtom/0.1/",
	"rel-tag" : "http://purl.org/uF/rel-tag/1.0/",
	"hcalendar" : "http://purl.org/uF/hCalendar/1.0/",
	"hresume" : "http://microformats.org/wiki/hresume-profile",
	"xfn" : "http://gmpg.org/xfn/11",
	"xfolk" : "http://microformats.org/wiki/xfolk-profile",
	"xCal" : "urn:ietf:params:xml:ns:xcal",
}

class APIBase(object):
	"""Base class for creating functions that can read from an API
	
	NOTE: a lot of these variables should be moved to APIReader
	"""

	_required_properties = [ "uri", ]
	_required_attributes = []
	_attributes = None

	_base_query = {}
	_item_path = None
	_verbose = 0

	## these limits are discovered on a per query basis using the paths below
	_page_max_path = None
	_page_max = 1

	_item_max_path = None
	_item_max = -1

	## user specified limits to number of results returned
	_item_limit = -1
	_page_limit = 3

	## all passed to bm_uri
	_http_referer = None
	_http_user_agent = None
	_http_ad = {}

	## the request ...
	_request_meta = {}
	_request_items = []

	## make results look like atom
	_atom_like = None
	_atom_item = None	## list of (from, to) tuple
	_atom_meta = None	## list of (from, to) tuple

	## the URI we are working with
	_uri_base = None
	_uri = None

	## ...
	_must_reset = True

	## authentication object
	_authenticate = None

	def __init__(self, **ad):
		self._atom_like = atom_like

		self.SetRequest(**ad)
		self._base_query.update(self._request_meta)

		self.Restart()

	def Restart(self):
		"""Restart an existing query"""

		## Log("Have Restart", verbose = True, _must_reset = self._must_reset)

		self._first_page = None
		self._page_index = 0
		self._item_index = -1
		self._validated = False

		self._page_max = 1
		self._item_max = -1

		self.CustomizeRestart()

	def Produced(self):
		"""You _must_ call this in subclasses if you're about to start producing results.
		It will flag that the next time the request is changed, the old request is cleared.
		If you are using APIReader, this is handled for you
		"""

		self._must_reset = True

	def AtomLike(self):
		return	self._atom_like == None or self._atom_like

	def CheckReset(self):
		## Log("Check Reset", verbose = True, _must_reset = self._must_reset)

		if self._must_reset:
			self.Restart()
			self._must_reset = False

			self._request_meta = {}
			self._request_meta.update(self._base_query)

			self.CustomizeReset()

	def SetRequest(self, **ad):
		self.CheckReset()

		for key, value in ad.iteritems():
			if self._attributes and key in self._attributes:
				self._request_meta[key] = value
			elif hasattr(self, key) or key in dir(self):
				setattr(self, key, value)
			else:
				self._request_meta[key] = value

	def SetItems(self, items):
		self.CheckReset()

	def SetURI(self, uri):
		self.CheckReset()

		self._uri_base = uri
		self._uri = uri

	def GetMeta(self):
		return	{}

	def IterItems(self):
		raise	StopIteration

	def CustomizeReset(self):
		pass

	def CustomizeRestart(self):
		pass

	def CustomizeValidate(self):
		for required in self._required_properties or []:
			if not hasattr(self, required) or not getattr(self, required):
				raise	ValueError, "missing property '%s' value" % required

		for required in self._required_attributes or []:
			if not self._base_query.get(required):
				raise	ValueError, "missing attribute '%s' value" % required

	def CustomizeAtomItem(self, itemd):
		if self._atom_item:
			for k_to, k_from in self._atom_item.iteritems():
				try:
					itemd[k_to] = itemd.pop(k_from)
				except KeyError:
					pass

		return	itemd

	def CustomizeAtomMeta(self, metad):
		if self._atom_meta:
			for k_to, k_from in self._atom_meta.iteritems():
				try:
					metad[k_to] = metad.pop(k_from)
				except KeyError:
					pass

		return	metad

	@apply
	def uri():
		def fset(self, uri):
			self.SetURI(uri)

		def fget(self):
			return	self._uri or self._uri_base

		return property(**locals())

	@apply
	def meta():
		def fget(self):
			return	self.GetMeta()

		return property(**locals())

	@apply
	def response():
		def fget(self):
			return	self.GetMeta()

		return property(**locals())

	@apply
	def request():
		def fset(self, metad):
			self.SetRequest(**bm_text.safe_parameterd(metad))

		return property(**locals())

	@apply
	def authenticate():
		def fset(self, service_name):
			d = bm_cfg.cfg.get(service_name)
			if not d:
				Log("warning - authentication service was not found: don't be surprised by an exception soon", service_name = service_name)
				return

			if d.get('oauth_consumer_key'):
				self._authenticate = bm_uri.Authenticate(
					auth = bm_oauth.OAuth(service_name = service_name)
				)
			elif d.get('username'):
				self._authenticate = bm_uri.Authenticate(
					auth = bm_uri.AuthBasic(
						username = bm_extract.as_string(d, 'username'),
						password = bm_extract.as_string(d, 'password'),
					)
				)

		return property(**locals())

	@apply
	def items():
		def fget(self):
			class generator:
				def __init__(self, f):
					self.f = f

				def __iter__(self):
					self.f.Restart()
					return	self.f.IterItems()

			return	generator(self)

		def fset(self, items):
			self._request_items = items

		return property(**locals())

class APIReader(APIBase):
	"""Base class APIs that directly downloads a URI and may have paged results"""

	_convert2work = bm_work.XML2WORK()
	_inject_position = True
	_meta_path = None
	_meta_removes = None

	def GetMeta(self):
		"""Return the Meta-WORK for a page

		* this can be subclassed to do whatever you want
		* if no pages, the result is null
		* if self._meta_path is defined, that path is extracted from the first page
		* otherwise, it's the first page
		"""

		resultd = {}

		for page in self._IterPage():
			if self._meta_removes:
				if self._meta_path:
					srcd = page.get(self._meta_path, {})
				else:
					srcd = page

				for key, value in srcd.iteritems():
					if key not in self._meta_removes:
						resultd[key] = value
			else:
				if self._meta_path:
					resultd = page.get(self._meta_path, {})
				else:
					resultd = page

			break

		if self.AtomLike():
			resultd = self.CustomizeAtomMeta(resultd)

		return	resultd

	def IterItems(self):
		"""Iterate through all the items"""

##		if not self._item_path:
##			raise	StopIteration
##			## raise	RuntimeError, "API Implementation Error: '_item_path' MUST be defined"

		for page in self._IterPage():
			for item in self._IterItemsOnPage(page):
				if item == None:
					continue

				self._item_index += 1
				if self._item_limit > -1 and self._item_index >= self._item_limit:
					raise	StopIteration

				if self._inject_position:
					item['@@Page'] = self._page_index
					item['@@Index'] = self._item_index

				if self.AtomLike():
					item = self.CustomizeAtomItem(item)

				yield	item

	def _IterPage(self):
		"""Iterate """

		self.Produced()

		if not self._validated:
			self.CustomizeValidate()
			self._validated = True

		if self._first_page:
			yield	self._first_page

		self._page_index = 0
		self._item_index = -1

		while True:
			self._page_index += 1

			page = self.CustomizeDownloadPage()
			if not page:
				break

			if not self._first_page:
				self._first_page = page
				self.CustomizeFirstPage(self._first_page)

			yield	page

			if self._page_limit > -1 and self._page_index >= self._page_limit:
				break

			if self._page_max > -1 and self._page_index >= self._page_max:
				break
	
	def _IterItemsOnPage(self, page):
		if self._item_path == None:
			raise	StopIteration

		if not self._item_path:
			for item in bm_extract.coerce_list(page):
				yield	item
		else:
			for item in bm_extract.as_list(page, self._item_path, otherwise = []):
				yield	item

	def ConstructPageURI(self):
		self._uri = self._uri_base

		if not self._uri:
			raise	ValueError, "missing 'uri'"
		
		join = self._uri.find('?') == -1 and "?" or "&"
		for key, value in self._request_meta.iteritems():
			if value == None:
				continue
			elif type(value) in types.StringTypes:
				self._uri += "%s%s=%s" % ( join, key, urllib.quote(value), )
			elif type(value) == types.ListType:
				self._uri += "%s%s=%s" % ( join, key, urllib.quote(",".join(value)), )
			elif isinstance(value, bm_extract.AsIs):
				if value.value == None:
					continue
				self._uri += "%s%s=%s" % ( join, key, value.value, )
			else:
				self._uri += "%s%s=%s" % ( join, key, value, )

			join = "&"

		page_modifier = self.CustomizePageURI(self._page_index)
		if page_modifier:
			self._uri += "%s%s" % ( join, page_modifier, )

		Log(_uri = self._uri, verbose = True)

		return	self._uri

	def CustomizeFirstPage(self, page):
		if self._page_max_path:
			self._page_max = bm_extract.as_int(page, self._page_max_path, otherwise = 1)

		if self._item_max_path:
			self._item_max = bm_extract.as_int(page, self._item_max_path, otherwise = -1)

	def CustomizePageURI(self, page_index):
		return

	def CustomizeDownloadPage(self):
		"""Called by _IterPage to get the next page"""

		try:
			loader = bm_uri.URILoader(
				self.ConstructPageURI(), 
				referer = self._http_referer,
				user_agent = self._http_user_agent,
				authenticate = self._authenticate,
				**self._http_ad
			)
			loader.Load()
		except bm_uri.NotModified:
			pass
		except bm_uri.DownloaderError:
			raise

		return	self._convert2work.FeedString(loader.GetRaw())

class XMLAPIWriter(APIBase):
	"""Base class for generating XML documents from WORK-like dictionarie"""

	namespaced = {}

	def __init__(self, **ad):
		self._e_root = None

		APIBase.__init__(self, **ad)

	def Produce(self):
		self._e_root = None

		self.CustomizeProduce()
		
		if self._e_root:
			self._namespaces()
			return	ElementTree.tostring(self._e_root, 'utf-8')

		raise	NotImplementedError, "CustomizeProduce did not create any XML objects"

	def SetRequest(self, **ad):
		"""We don't use properties in XMLAPI, so we override"""

		for key, value in ad.iteritems():
			self._request_meta[key] = value

	def GetMeta(self):
		"""Just return what was set..."""
		return	self._request_meta

	def IterItems(self):
		"""Just return what was set..."""
		return	self._request_items

	def CustomizeProduce(self):
		"""Do the work of making the XML, by calling TranscribeNode and MakeElement
		If this is not overridden, Produce must be
		"""

	def TranscribeNode(self, e_node, o):
		"""Convert a dictionary into XML"""

		if bm_extract.is_list(o):
			for sub in o:
				self.TranscribeNode(e_node, sub)
		elif bm_extract.is_dict(o):
			#
			#	Get the attributes
			#
			ad = {}
			for key, sub in o.iteritems():
				if key.startswith("@@") or key.find(":@@") > -1:
					continue

				if key == '@':
					e_node.text = bm_extract.coerce_string(sub, separator = ",")
					continue

				if key.startswith("@") or key.find(":@") > -1:
					if bm_extract.is_atomic(sub):
						e_node.set(key.replace('@', ''), bm_extract.coerce_string(sub))
						## ad[key.replace('@', '')] = bm_extract.coerce_string(sub)
					elif bm_extract.is_list(sub) or bm_extract.is_list_like(sub):
						e_node.set(key.replace('@', ''), bm_extract.coerce_string(sub, separator = ","))
						## ad[key.replace('@', '')] = bm_extract.coerce_string(sub, separator = ",")

			#
			#	Note here that:
			#	- @@ means an attribute it hidden
			#	- @ are attributes, and are found in the previous step
			#	- lists are processed specially, as they result in repeated children
			#
			for key, sub in o.iteritems():
				if key.startswith("@@") or key.find(":@@") > -1:
					continue

				if key.startswith("@") or key.find(":@") > -1:
					continue

				#
				#
				#
				if bm_extract.is_list_like(sub):
					sub = list(sub)

				if bm_extract.is_list(sub):
					any = False
					for subsub in sub:
						any = True

						e_child = ElementTree.SubElement(e_node, key)
						self.TranscribeNode(e_child, subsub)

					if any:
						continue

					sub = None

				#
				#
				#
				e_child = ElementTree.SubElement(e_node, key)
				self.TranscribeNode(e_child, sub)
		elif bm_extract.is_list_like(o):
			for sub in list(o):
				self.TranscribeNode(e_node, sub)
		elif bm_extract.is_none(o):
			pass
		else:
			if e_node.text:
				e_node.text += "\n"
				e_node.text += bm_extract.coerce_string(o)
			else:
				e_node.text = bm_extract.coerce_string(o)

	def MakeElement(self, name, parent = None):
		if parent == None:
			self._e_root = ElementTree.Element(name)
			return	self._e_root
		else:
			return	ElementTree.SubElement(parent, name)

	def _tostring(self, element):
		return	ElementTree.tostring(element, 'utf-8')

	def _namespaces(self):
		namespaces = sets.Set()

		for e in self._e_root.getiterator():
			cx = e.tag.find(':')
			if cx != -1:
				namespaces.add(e.tag[:cx])

			for key in e.keys():
				cx = key.find(':')
				if cx != -1:
					namespaces.add(key[:cx])

		for namespace in namespaces:
			uri = self.namespaced.get(namespace)
			if not uri:
				Log("WARNING - namespace not found", namespace = namespace)
				uri = "#%s" % namespace

			self._e_root.set("xmlns:%s" % namespace, uri)

		Log(namespaces = namespaces, verbose = True)

	def Separate(self, itemd, knowns, namespace):
		"""Helper function for subclasses to deal with namespaced objects

		Parameters:
		itemd - the item to separate, a dictionary
		knowns - known field names, a dictionary
		namespace - the default namespace we are working in

		Returns
		- ( known-dictionary, unknown-dictionary )
		"""

		nd = {}
		xd = {}

		for key, value in itemd.iteritems():
			if not value:
				continue

			if key.startswith("%s:" % namespace):
				key = key[len(namespace) + 1:]

			if not key in knowns and key.find(':') == -1:
				xd[key] = value
				continue

			nd[key] = value

		return	nd, xd

#
#	Helper functions below here
#
def add_latlon(d, lat, lon):
	lat = bm_extract.coerce_float(lat, otherwise = None)
	lon = bm_extract.coerce_float(lon, otherwise = None)

	if lat == None or lon == None:
		return

	d["georss:point"] = [ lat, lon ]
