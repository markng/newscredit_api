#
#	bm_uri.py
#
#	David Janes
#	2006.01.03
#

"""read stuff from URIs with the potential to cache

Required: Python 2.3 or later
"""

import sys
import os
import os.path
import cgi
import pprint
import types
import re
import urllib
import urllib2
import urlparse
import md5
import time
import socket
import cPickle as pickle

import bm_extract
import bm_io
import bm_text
import bm_cfg

from bm_log import Log

error_socket_timeout = False

class DownloaderError(Exception):
	pass

class TooBigError(DownloaderError):
	def __init__(self, msg = ""):
		Exception.__init__(self, msg)

class Unavailable(DownloaderError):
	def __init__(self, msg = ""):
		Exception.__init__(self, msg)

class NotModified(DownloaderError):
	def __init__(self):
		Exception.__init__(self)

VAR_ROOT = "."
try:
	import bm_config
	VAR_ROOT = bm_config.BM_VAR_ROOT
except ImportError:
	VAR_ROOT = os.getenv("HOME", ".")


#
#	Do not manipulate directly, use:
#
#	Rules.Global().Set(None, user_agent : "...", "min_retry" : 4000) (etc)
#
config = {
	#
	#	The User-Agent sent in the HTTP headers
	#
	"user_agent" : "pybm.bm_uri loader 0.2 (http://code.google.com/p/pybm/)",

	#
	#	If we have a copy of the document and it's less than
	#	this period of time, just return the document
	#
	"min_retry" : 60 * 5,

	#
	#	Get a fresh copy -- ignore Last-Modified and ETag -- if more
	#	than this time has passed
	#
	"max_retry" : 60 * 60 * 24 * 30,

	#
	#	DB directory
	#
	"db_dir" : os.path.join(VAR_ROOT, "bm_uri"),

	#
	#	HTMLLoader -- use 'tidy' to fix up HTML document
	#
	"use_tidy" : True,

	#
	#	If you want the cached files to be split into subdirectories,
	#	set this to something like 3 or 4.
	#
	"path_split" : 3,

	#
	#	If Unavailable, how many times to retry
	#
	"retries" : 0,

	#
	#	# of seconds to wait between retries
	#
	"retry_delay" : 5,

	#
	#	how long to wait for a socket to open
	#
	"socket_timeout" : 15,

	#
	#	maximum download
	#
	"max_download" : 1024 * 1024 * 1024,

	#
	#	if the maximum download is reached, pretend it's OK
	#
	"soft_max" : False,
}

#
#	Rules
#
class Rules:
	"""Host specific rule sets.
	
	Rules cover all the information above in 'config', and control items such as
	the User-Agent, how often to download URIs, etc.
	"""

	ruled = {}

	def Add(self, hostname = None, **ad):
		"""Add config rules for the hostname. If hostname is empty, it is
		assumed the rules will apply to all hosts.
		If hostname is a URL, the hostname will be extracted. Do not add colons
		"""

		## ... nasty hobbitesses
		for key in [ "db_dir", "path_split", ]:
			try: del ad[key]
			except: pass

		self.ruled[self._scrub(hostname)] = ad
		
	def Find(self, hostname = None):
		"""Look up a hostname and return the ( username, password ) tuple, or {}"""

		return	self.ruled.get(self._scrub(hostname)) or {}
		
	@classmethod
	def Global(cls):
		"""The globally available rules. Generally you
		will use this be if need by you can pass an Authenticate object
		to URILoader to override"""

		return	global_rules

	def _scrub(self, hostname):
		if not hostname:
			return	"";

		if hostname.find('/') > -1:
			hostname = host(hostname)

		colonx = hostname.find(':')
		if colonx != -1:
			hostname = hostname[:colonx]

		return	hostname

global_rules = Rules()

charset_re = ";\s*charset=([-a-zA-Z_0-9]+)"
charset_rex = re.compile(charset_re)

ctype_re = "([^;]*)"
ctype_rex = re.compile(ctype_re)

debug_forced = {}

realm_re = 'Basic realm="(?P<realm>[^"]*)"'
realm_rex = re.compile(realm_re, re.I)

#
#	Authentication
#
class Auth:
	def __init__(self, service_name = None, cfg = None, api_uri = None):
		self.request = None
		self.service_name = service_name
		self.cfg = cfg
		self.api_uri = api_uri

	def Connect(self, loader):
		self.BuildRequest(loader)
		self.AddHeaders(loader)
		return	self.Open(loader)

	def BuildRequest(self, loader):
		if loader.method == "POST":
			d = {}
			for key, value in (loader.data or {}).iteritems():
				d[bm_text.toutf8(key)] = bm_text.toutf8(value)

			self.request = urllib2.Request(loader.uri, data = urllib.urlencode(d))
		else:
			self.request = urllib2.Request(loader.uri)

	def AddHeaders(self, loader):
		etag = loader.headers.get('etag')
		if etag:
			self.request.add_header("If-None-Match", etag)

		modified = loader.headers.get('modified')
		if modified:
			self.request.add_header("If-Modified-Since", format_http_date(modified))

		self.request.add_header("User-Agent", loader.config["user_agent"])
		self.request.add_header("Pragma", "no-cache")
		self.request.add_header("Cache-Control", "no-cache")

		if loader.config.get('referer'):
			self.request.add_header("Referer", loader.config["referer"])

	def Open(self, loader):
		Log("Auth: downloading", uri = loader.uri, verbose = True, cname = self.__class__.__name__)

		return	urllib2.urlopen(self.request)

class AuthNone(Auth):
	def __init__(self, service_name = None, cfg = None, api_uri = None, **ad):
		Auth.__init__(self, service_name = service_name, cfg = cfg, api_uri = api_uri)

class AuthBasic(Auth):
	def __init__(self, username = None, password = None, service_name = None, cfg = None, api_uri = None):
		Auth.__init__(self, service_name = service_name, cfg = cfg, api_uri = api_uri)

		self.username = username
		self.password = password

		if self.service_name:
			self.LoadCfg()

	def LoadCfg(self):
		cfg = self.cfg or bm_cfg.cfg

		if not self.service_name:
			raise	ValueError("service_name is required during initialization")

		d = cfg.get(self.service_name)
		if not d:
			Log("did not find service in bm_cfg", name = self.service_name)
			return

		self.username = self.username or bm_extract.as_string(d, "username")
		self.password = self.username or bm_extract.as_string(d, "password")

		api_uri = self.api_uri or d.get("api_uri")
		if api_uri:
			Authenticate.Global().Add(api_uri, self)

	def Open(self, loader):
		nin = None

		assert(type(self.username) in types.StringTypes), "'username' is required"
		assert(type(self.password) in types.StringTypes), "'password' is required"

		try:
			Log("AuthBasic: downloading", uri = loader.uri, verbose = True)
			nin = urllib2.urlopen(self.request)
		except urllib2.HTTPError, x:
			#
			#	This is our 401 WWW-Authenticate Basic Realm handler
			#
			if x.code != 401:
				raise
				
			username_password = (loader.authenticate or Authenticate.Global()).Find(loader.uri)
			if not username_password:
				raise

			#
			#	Discover the realm, which we'll need for HTTP auth
			#
			realm_value = x.headers.get("WWW-Authenticate")
			if not realm_value:
				raise
				
			realm_match = realm_rex.match(realm_value)
			if not realm_match:
				raise
				
			realm = realm_match.group('realm')
			Log(realm = realm, verbose = True)

			#
			#	add the handler
			#
			auth_handler = urllib2.HTTPBasicAuthHandler()
			auth_handler.add_password(
				realm = realm,
				uri = loader.uri,
				user = self.username,
				passwd = self.password,
			)

			opener = urllib2.build_opener(auth_handler)
			urllib2.install_opener(opener)

			#
			#	Try and reload
			#
			nin = opener.open(self.request)
			
			#
			#	If 'cachable' is None, we don't save results
			#	that use authorization. 
			#
			if loader.cachable == None:
				loader.do_cache = False

		assert(nin)
		return	nin

class Authenticate:
	"""Username/passwords for websites (by 'hostname')
	"""
	authd = {}

	def __init__(self, auth = None):
		self.otherwise = auth or AuthNone()
	
	def Add(self, uri, auth):
		for _uri in bm_extract.coerce_list(uri):
			self.authd[_uri.rstrip("/") + "/"] = auth
		
	def Find(self, uri):
		uparts = urlparse.urlparse(uri)
		prefix = "%s://%s" % ( uparts.scheme, uparts.netloc )
		path = uparts.path or "/"

		while True:
			uri = "%s%s/" % ( prefix, path.rstrip("/"), )

			a = self.authd.get(uri)
			if a:
				return	a

			npath = os.path.dirname(path)
			if not npath or npath == path:
				break

			path = npath

		return	self.otherwise
		
	@classmethod
	def Global(cls):
		"""The globally available authentication rules. Generally you
		will use this be if need by you can pass an Authenticate object
		to URILoader to override"""

		return	global_authenticate

global_authenticate = Authenticate()

#
#
#
class URILoader:
	"""Load data from a URI, being clever with caching to avoid reloading.

	Data downloaded from the URI is called 'raw'. Whenever data is downloaded,
	we invoke a function called 'Cook' which returns the cooked data -- this can
	any _basic_ python data structure (it needs to be writable to disk as
	a string)
	"""

	def __init__(self, 
		uri, 
		loader = None, 
		authenticate = None, 
		rules = None, 
		method = None,
		data = None, 
		cachable = None, 
		**cfg):
		"""Declare that we are going from the 'uri'. Any remaining named parameters can override
		the configuration. Call 'Load' to do the actual work
		"""

		self.uri, fragment = urlparse.urldefrag(uri)

		#
		#	We can use this to POST, but these are cachable results
		#	only very rare circumstances
		#
		if method == None:
			if data == None:
				method = "GET"
			else:
				method = "POST"

				if cachable == None:
					cachable = False

		self.method = method
		self.data = data
		self.cachable = cachable
		self.do_cache = False

		self.authenticate = authenticate or Authenticate.Global()
		self.rules = rules or Rules.Global()

		self.parent = None
		if loader:
			self.parent = loader

		self.Reset()

		#
		#	Order of config rules, from least important to most import
		#	- config                ... the module predefined defaults
		#	- self.rules.Find()     ... the config for all hostnames
		#	- self.rules.Find(uri)  ... the config for this URI
		#	- cfg                   ... the config passed in during construction
		#
		#	The rules are typically the global rules defined by Rules.Global(),
		#	but they can be overriden (entirely!) by the rules parameter.
		#
		self.config = dict(config)
		self.config.update(self.rules.Find(None))
		self.config.update(self.rules.Find(uri))
		self.config.update(cfg)

		Log(config = self.config, verbose = True, uri = self.uri)

		hash = urc(self.uri, self.method, pprint.pformat(self.data))
		split = min(4, max(0, self.config["path_split"]))

		self.db_prefix = os.path.join(self.config["db_dir"], hash[:split], hash[split:] + ".")
		self.db_header_path = self.db_prefix + "pyd"
		self.db_raw_path = self.db_prefix + "raw"
		self.db_cooked_path = self.db_prefix + self.__class__.__name__

		try: os.makedirs(self.config["db_dir"])
		except: pass
		
	def Reset(self):
		self.status = 0
		self.reason = ""

		self.headers = {}

		self.raw = None
		self.cooked = None
		
	def Load(self, raw = None, exception = True):
		self.raw = None

		count = -1
		while True:
			count += 1

			try:
				self._Load(raw = raw)
				break
			except Unavailable, x:
				if not self.config["retries"] or count > self.config["retries"]:
					if exception:
						raise	x
					else:
						return	self.raw

				Log("retrying",
					exception = True,
					uri = self.uri,
					count = count,
					retries = self.config["retries"],
					retry_delay = self.config["retry_delay"],
				)
					
				time.sleep(self.config["retry_delay"])
			except KeyboardInterrupt:
				raise
			except SystemExit:
				raise
			except:
				if exception:
					raise
				else:
					return	None

		return	self.raw

	def _Load(self, raw = None):
		"""Open the URI (or get it from the cache) and read it in it's entirety"""

		is_authorized = None

		#
		#	By default, we cache - we can turn this off in a number
		#	of places through the process. do_cache == None means we're
		#	indifferent, True means cache if at all reasonable, False
		#	means never.
		#
		self.do_cache = True
		if self.cachable == False:
			self.do_cache = False

		forced = debug_forced.get(self.uri)
		if forced:
			Log("using forced URI", uri = self.uri, ldata = len(forced))
			raw = forced
			self.do_cache = False

		self.Reset()
		self.LoadFromDB()

		if self.headers and raw == None:
			x_saved = bm_extract.coerce_float(self.headers.get("X-Saved"), 0)
			x_status = bm_extract.as_int(self.headers, "X-Status", otherwise = 200)
			x_reason = bm_extract.as_string(self.headers, "X-Reason")

			Log(	
				x_saved = True,
				delta_saved = time.time() - x_saved,
				min_retry = self.config["min_retry"],
				max_retry = self.config["max_retry"],
				verbose = True,
				uri = self.uri,
			)
			if time.time() - x_saved < self.config["min_retry"]:
				if x_status != 200:
					self.status = x_status
					self.reason = x_reason

					raise   Unavailable("%s: %s" % ( x_status, x_reason ))

				return

			if time.time() - x_saved >= self.config["max_retry"]:
				self.headers = {}
				self.raw = None
				self.cooked = None

		if raw and self.raw != raw:
			self.cooked = None


		#
		#	Headers during a thrown exception
		#
		x_headers = None

		try:
			try:
				if raw:
					nin = None
					self.raw = raw
					self.status = 200
					self.reason = "OK"
				else:
					try:
						try:
							try:
								old_timeout = socket.getdefaulttimeout()
								socket.setdefaulttimeout(self.config["socket_timeout"])
							except:
								global error_socket_timeout
								if not error_socket_timeout:
									error_socket_timeout = True
									Log("error setting timeout", exception = True, config = self.config)

							#
							#	Authenticate/Connection Manager object
							#
							auth = (self.authenticate or Authenticate.Global()).Find(self.uri)
							assert(auth), "Authenticate is _guarenteed to return an Auth object!"

							#
							#	Connect....
							#
							nin = auth.Connect(self)
						finally:
							try: socket.setdefaulttimeout(old_timeout)
							except: pass
							
					except urllib2.HTTPError, x:
						if x.code == 304 and self.raw:
							raise   NotModified()

						self.status = x.code
						self.reason = x.msg

						x_headers = dict(x.headers)

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))
					except urllib2.URLError, x:
						self.status = 500
						self.reason = x.reason

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))
					except KeyboardInterrupt:
						raise
					except SystemExit:
						raise
					except:
						self.status = 500
						self.reason = Log("unknown failure", exception = True)

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))

					try:
						raws = []
						nbytes = 0
						while nbytes < self.config['max_download']:
							raw = nin.read(min(self.config['max_download'] - nbytes, 32 * 1024))
							if not raw:
								break

							raws.append(raw)
							nbytes += len(raw)

						self.raw = "".join(raws)

						if nbytes == self.config['max_download'] and not self.config['soft_max'] and nin.read(1):
							raise	TooBigError("exceeded %d bytes" % self.config['max_download'])
					except socket.timeout, x:
						self.status = 500
						self.reason = "Socket timeout"

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))
					except socket.error, x:
						self.status = 500
						self.reason = "socket problem: %s" % str(x)

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))
					except TooBigError:
						raise
					except KeyboardInterrupt:
						raise
					except SystemExit:
						raise
					except:
						self.status = 500
						self.reason = Log("unknown failure", exception = True)

						raise   Unavailable("%s: %s" % ( self.status, self.reason ))
			finally:
				try: nin.close()
				except: pass

			#
			#	This can be deleted?
			#
			if raw:
				self.cooked = self.Cook(self.raw)

			self.headers = ( nin and dict(nin.info()) ) or ( self.parent and self.parent.headers and dict(self.parent.headers) ) or {}
			self.headers["X-URI"] = self.uri

			if self.do_cache:
				self.SaveRawToDB()
		except NotModified:
			self.status = 400
			self.reason = ""

			#
			#	If we are here, we resave the header so we don't connect again!
			#
			if self.do_cache:
				self.SaveRawToDB(raw = False, clear = False)

			return
		except Unavailable:
			if self.headers:
				self.status = 400
				self.reason = ""

				return

			#
			#	Certain failures can be cached
			#
			if self.status in [ 404, ] and self.do_cache:
				try:
					old_headers = self.headers
					old_raw = self.raw

					self.headers = x_headers
					self.headers["X-Status"] = self.status
					self.headers["X-Reason"] = self.reason
					self.raw = ""

					self.SaveRawToDB()
				finally:
					self.headers = old_headers
					self.raw = old_raw

			raise

	def Cook(self, raw):
		"""Redefine me to return something interesting"""
		return	None

	def GetRaw(self):
		return  self.raw

	def GetCooked(self):
		if self.cooked != None:
			return	self.cooked

		self.cooked = self.Cook(self.raw)

		try:
			return	self.cooked
		finally:
			try:
				if self.cooked != None and self.do_cache:
					self.SaveCookedToDB()
			except:
				Log("this exception should never happen", exception = True)

	def GetHeader(self, key, otherwise = None):
		return	self.headers.get(key, otherwise)

	def GetHeaders(self):
		return	self.headers

	def IsOK(self):
		return	self.raw != None

	def GetStatus(self):
		return	self.status

	def GetReason(self):
		return	self.reason

	def GetCharset(self, otherwise = None):
		ctype = self.headers.get("content-type")
		if not ctype:
			return	otherwise

		match = charset_rex.search(ctype)
		if match and match.group(1):
			return	match.group(1)

		return	otherwise

	def GetContentType(self, otherwise = None):
		ctype = self.headers.get("content-type")
		if not ctype:
			return	otherwise

		match = ctype_rex.search(ctype)
		if match and match.group(1):
			return	match.group(1).strip()

		return	otherwise

	def IsHTML(self):
		if self.GetContentType() in [ "text/html", "text/xhtml", "application/xhtml", ]:
			return	True

		if self.raw:
			begin = self.raw[:256].lower()

			if begin.find('<html') > -1:
				return	True

			## google search results, sometimes...
			if begin.find('<!doctype html>') > -1:
				return	True

		Log("WARNING - returning False; this page isn't HTML", uri = self.uri)
		return	False

	def LoadFromDB(self):
		try:
			if os.path.exists(self.db_header_path):
				try:
					hin = open(self.db_header_path, 'rb')
					try:
						self.headers = pickle.load(hin)
					except pickle.PickleError:
						Log("unexpected exception reading header -- will ignore cached data",
							len_data = len(data),
							data = repr(data[:256]),
							path = self.db_header_path,
						)
						bm_io.remove(self.db_header_path, silent = True)
						bm_io.remove(self.db_cooked_path, silent = True)
						raise
				finally:
					try: hin.close()
					except: pass

			if os.path.exists(self.db_raw_path):
				try:
					rin = open(self.db_raw_path, 'rb')
					self.raw = rin.read()
				finally:
					try: rin.close()
					except: pass

			if os.path.exists(self.db_cooked_path):
				try:
					cin = open(self.db_cooked_path, 'rb')
					try:
						self.cooked = pickle.load(cin)
					except pickle.PickleError:
						Log("unexpected exception reading data -- will ignore cached data",
							len_data = len(data),
							data = repr(data[:256]),
							path = self.db_cooked_path,
						)
						bm_io.remove(self.db_header_path, silent = True)
						bm_io.remove(self.db_cooked_path, silent = True)
						raise
				finally:
					try: cin.close()
					except: pass
		except SyntaxError:
			Log(exception = True)
			self.raw = None
			self.headers = {}
		except:
			Log("unexpected exception -- ignorning", exception = True)

			self.raw = None
			self.headers = {}

	def SaveRawToDB(self, header = True, raw = True, clear = True):
		try:
			if clear:
				try:
					prefix_dir, prefix_base = os.path.split(self.db_prefix)
					if os.path.exists(prefix_dir):
						for file in os.listdir(prefix_dir):
							if file.startswith(prefix_base):
								bm_io.remove(os.path.join(prefix_dir, file), silent = False)
				except:
					Log("ignoring exception", exception = True)

			if header:
				self.headers["X-Saved"] = "%d" % ( time.time(), )

				try:
					hout = bm_io.AtomicWrite(self.db_header_path, 'wb', makedirs = True)
					pickle.dump(self.headers, hout)
				finally:
					try: hout.close()
					except: pass

			if raw:
				try:
					rout = bm_io.AtomicWrite(self.db_raw_path, 'wb', makedirs = True)
					rout.write(self.raw)
				finally:
					try: rout.close()
					except: pass
		except OSError:
			Log("this is important but I think we can ignore it for now", exception = True)

	def SaveCookedToDB(self):
		try:
			try:
				cout = bm_io.AtomicWrite(self.db_cooked_path, 'wb', makedirs = True)
				try:
					pickle.dump(self.cooked, cout)
				except:
					Log(exception = True, cooked = self.cooked)
			finally:
				try: cout.close()
				except: pass
		except OSError:
			Log("this is important but I think we can ignore it for now", exception = True)

	def Clean(self):
		for path in [ self.db_header_path, self.db_raw_path, self.db_cooked_path ]:
			if path:
				bm_io.remove(path)

	@classmethod
	def ForceURIValue(cls, uri, raw):
		global debug_forced
		debug_forced[uri] = raw

html_head_re = """<html.*<head(.*?)</head>"""
html_head_rex = re.compile(html_head_re, re.I|re.DOTALL|re.MULTILINE)

html_comment_re = """<!\s*--(.*?)-->"""
html_comment_rex = re.compile(html_comment_re, re.I|re.MULTILINE|re.DOTALL)

html_meta_re = """<\s*meta\s+([^>]*?)\s*>"""
html_meta_rex = re.compile(html_meta_re, re.I|re.MULTILINE|re.DOTALL)

http_namecontent_re = """(name|content)\s*=\s*('([^']*)'|"([^"]*")|[^\s]*)"""
http_namecontent_rex = re.compile(http_namecontent_re, re.I|re.MULTILINE|re.DOTALL)

http_equiv_re = """http-equiv[^\s=]*\s*=\s*['"]*content-type["']*"""
http_equiv_rex = re.compile(http_equiv_re, re.I|re.MULTILINE|re.DOTALL)

http_charset_re = """charset\s*=\s*([^\s"';]*)"""
http_charset_rex = re.compile(http_charset_re, re.I|re.MULTILINE|re.DOTALL)


class HTMLLoader(URILoader):
	"""This extends URILoader to understand HTML documents. The result is an unicode string
	that is hopefully HTML/XHTML compliant.
	"""

	def __init__(self, uri, **cfg):
		"""
		Set 'use_tidy = False' if you don't want XHTML post processing
		"""
		URILoader.__init__(self, uri, **cfg)

	def Cook(self, raw):
		if not raw:
			return	u""

		if not self.IsHTML():
			return	u""

		if self.config["use_tidy"]:
			#
			#	Get the charset from the HEAD
			#
			html_charset = None
			html_head_match = html_head_rex.search(raw)
			if html_head_match:
				html_head = html_head_match.group(0)
				html_head = html_comment_rex.sub("", html_head)

				for match in html_meta_rex.finditer(html_head):
					meta_data = match.group(1)

					name = ""
					content = ""
					for match in http_namecontent_rex.finditer(meta_data):
						value = match.group(2)
						if value[:1] == '"' and value[-1:] == '"': value = value[1:-1]
						elif value[:1] == "'" and value[-1:] == "'": value = value[1:-1]

						if match.group(1) == "name": name = value
						elif match.group(1) == "content": content = value

					if not http_equiv_rex.match(meta_data):
						continue

					charset_match = http_charset_rex.search(meta_data)
					if charset_match:
						html_charset = charset_match.group(1)
						break

			done = False
			if html_charset:
				try:
					raw = raw.decode(html_charset).encode('ascii', 'xmlcharrefreplace')
					done = True
				except:
					Log("ignoring this exception", exception = True, charset = html_charset)

			http_charset = self.GetCharset()
			if not done and http_charset:
				try:
					raw = raw.decode(http_charset).encode('ascii', 'xmlcharrefreplace')
					done = True
				except:
					Log("ignoring this exception", exception = True, charset = http_charset)

			# XXX - use pilgrim's library here
			if not done:
				try:
					raw = raw.decode('utf-8').encode('ascii', 'xmlcharrefreplace')
					done = True
				except:
					Log("ignoring this exception", exception = True, charset = http_charset)

			if not done:
				raw = raw.decode('latin-1').encode('ascii', 'xmlcharrefreplace')

			Log("trying TIDY", cmd = "tidy -asxml -n -i -w 128 -q -e -utf8", uri = self.uri)
			try:
				( child_stdin, child_stdout ) = os.popen2("tidy -asxml -n -i -w 128 -q -utf8 2> /dev/null")

				child_stdin.write(raw)
				child_stdin.close()

				document = child_stdout.read()
				if document:
					return	document.decode('utf-8')
			except IOError, y:
				Log("Exception calling TIDY", exception = True, traw = type(raw), lraw = len(raw))

		#
		#	Try to decode the document -- we should really be looking
		#	at the document's CHARSET internally coded, but I'm lazy for now
		#
		charset = self.GetCharset()
		if charset:
			try:
				return	raw.decode(charset)
			except:
				pass

		try:
			return	raw.decode('utf-8')
		except:
			pass

		try:
			return	raw.decode('iso-8859-1')
		except:
			pass

		return	raw.decode('iso-8859-1', 'replace')

try:
	try:
		import json
	except ImportError:
		import simplejson as json

	class JSONLoader(URILoader):
		def Cook(self, raw):
			if not raw:
				return	{}

			return	json.loads(raw)
except ImportError:
	pass

class TextLoader(URILoader):
	def __init__(self, uri, **cfg):
		URILoader.__init__(self, uri, **cfg)

	def Cook(self, raw):
		if not raw:
			return	u""

		charset = self.GetCharset()
		if charset:
			try:
				return	raw.decode(charset)
			except:
				pass

		try:
			return	raw.decode('utf-8')
		except:
			pass

		try:
			return	raw.decode('iso-8859-1')
		except:
			pass

		return	raw.decode('iso-8859-1', 'replace')

try:
	import bm_feedparser

	class FeedLoader(URILoader):
		def __init__(self, uri, **cfg):
			URILoader.__init__(self, uri, **cfg)

		def Cook(self, raw):
			try:
				rd = dict(bm_feedparser.parse(raw))

				try: del rd['bozo_exception']
				except: pass

				return	rd
			except Exception, x:
				Log("could not parse data from URI", uri = self.uri, exception = True)
				raise
except ImportError:
	pass

#
#	General helper functions
#
def normalize(uri):
	"""Simple guarenteed changes:
	- domain to lower case
	- remove stupid 'feed:' domain
	- remove port ':80'

	Probably should restrict this to HTTP://
	"""
	if not uri:
		return	uri

	for lstrip in [ ( 'feed://http//', 'http://' ), ( 'feed://https//', 'http://' ), ( 'feed:', 'http:', )]:
		if uri.startswith(lstrip[0]):
			uri = lstrip[1] + uri[len(lstrip[0]):]
			break

	urit = list(urlparse.urlparse(uri))

	urit[1] = urit[1].lower()
	if urit[1].endswith(":80"):
		urit[1] = urit[:-3]
	
	return	urlparse.urlunparse(urit)

to_strip = [
	"index.html",
	"index.htm",
	"index.shtml",
	"index.jsp",
	"index.php",
	"/.",
	"/",
]

def trim(uri, fragment = True, query = True):
	"""Return a pretty looking string based on a URI"""
	if not uri: return ""
	uri = uri.strip()
	if not uri: return ""

	if uri[:7] == "http://": uri = uri[7:]
	if uri[:4] == "www.": uri = uri[4:]

	altered = True
	while uri and altered:
		altered = False

		for s in to_strip:
			if uri[-len(s):].lower() == s:
				uri = uri[:-len(s)]
				altered = True
				break

	if not fragment and uri.rfind('#') > -1:
		uri = uri[:uri.rfind('#')]

	if not query and uri.rfind('?') > -1:
		uri = uri[:uri.rfind('?')]

	return	uri

def canonical(uri, keep_fragment = False):
	"""Convert a URI to a canonical form to help comparisons

	DO NOT use this URI for connecting. This is just a 99.5%
	correct solution for common aliases.
	"""
	if type(uri) == types.UnicodeType:
		uri = uri.encode('utf-8')

	scheme, host, path, x1, query, fragment = urlparse.urlparse(uri)

	scheme = scheme.lower()
	if scheme not in [ "http", "https", ]:
		return  uri

	host = host.lower()
	if host.endswith(":80"): host = host[:-3]
	if host.startswith("www."): host = host[4:]

	path = os.path.normpath(path)
	path = path.replace("\\", "/")
	if path == ".": path = ""

	for useless in to_strip:
		if path.lower().endswith(useless):
			path = path[:-len(useless)]
			break

	if not keep_fragment:
		fragment = ''

	return  urlparse.urlunparse(( scheme, host, path, '', query, fragment ))

def nofragment(uri):
	"""Remove the fragment from the URI"""
	if not uri:
		return	""

	ref_split = urlparse.urldefrag( urllib.unquote( uri ) )
	return ref_split[0]

	#"""Remove the fragment from the URI"""
	#if not uri:
	#	return	""
	#else:
	#	hashx = uri.find('#')
	#	if hashx > -1:
	#		return	uri[:hashx]
	#	else:
	#		return	uri

def host(uri, trim = False, trim_top = False):
	urit = urlparse.urlparse(uri)

	colonx = urit[1].find(':')
	if colonx == -1:
		host = urit[1]
	else:
		host = urit[1][:colonx]

	if trim:
		if host.startswith("www."):
			host = host[4:]
		elif host.startswith("rss."):
			host = host[4:]

	if trim_top:
		dx = host.rfind('.')
		if dx > -1:
			host = host[:dx]

	return	host

#
# Same as urlparse.urlsplit, but also split off the port number and return a new tuple with the port as the
# last item
#
def urlsplit( uri, default_scheme = '', allow_fragments = 1 ):
	"""split the url into a tuple of (scheme,net location,path,parameters,fragment,port #)"""
	uri_split = urlparse.urlsplit( urllib.unquote( uri ), default_scheme, allow_fragments )

	name_split = uri_split[1].split( ":" )
	if len( name_split ) < 2:
		name_split = [ name_split[0], '' ]

	return ( uri_split[0], name_split[0], uri_split[2], uri_split[3], uri_split[4], name_split[1] )

#
# Same as urlparse.urlunsplit, but uses the tuple from bm_uri.urlsplit
#
def urlunsplit( uri_tuple, quote = False ):
	"""merge the tuple from bm_uri.urlsplit (scheme,net location,path,parameters,fragment,port #) into a url string"""
	if uri_tuple[5]:
		uri_tuple = ( uri_tuple[0], "%s:%s" % ( uri_tuple[1], uri_type[5] ), uri_tuple[2], uri_tuple[3], uri_tuple[4] )
	else:
		uri_tuple = ( uri_tuple[0], uri_tuple[1], uri_tuple[2], uri_tuple[3], uri_tuple[4] )

	url = urlparse.urlunsplit( uri_tuple )
	if quote :
		url = urllib.quote( url )

	return url

quoted_re = """^.*(%[\da-fA-F][\da-fA-f]).*$"""
quoted_rex = re.compile(quoted_re)

pct_quoted_re = """^.*(%25).*$"""
pct_quoted_rex = re.compile(pct_quoted_re)

#
# Is the uri encoded, or in the urllib terminology quoted
#
def is_quoted( uri ):
	"""is the uri/string html encoded (quoted)"""
	match = quoted_rex.search(uri)
	if not match:
		return False

	return True

#
# Is the uri encoded, or in the urllib terminology quoted
#
def is_pct_quoted( uri ):
	"""is the uri/string html encoded (quoted)"""
	match = pct_quoted_rex.search(uri)
	if not match:
		return False

	match = None
	return True

#
# unquote a uri that has been multiply quoted
# accounts for pathological cases such as google%2520base%2F where %25 = % (is encoded)
# colapse all %25's in the string
#
def unquote( uri ):
	"""unquote a uri that has been multiply quoted """
	while is_pct_quoted( uri ):
		uri = uri.replace( '%25', '%' )

	return urllib.unquote( uri )

#
# Take a url and return the network location with no port number
#
def urlstrip( uri ):
	"""Take a url and return the network location with no port number"""
	uri_split = urlsplit( uri )
	return uri_split[ 1 ]

def scheme(uri, default = None):
	"""Return the 'scheme' of a URI"""
	return	urlparse.urlparse(uri)[0] or default

def is_downloadable_uri(uri):
	"""Can we work with this URI as is?"""
	return	scheme(uri) in [ "http", "https", "ftp", ]

def urc(*uris):
	"""A URC is a of converting URIs into a MD5 hash code for use
	as an identifier code. Many URIs or even other data items
	can be feed together to 'uniquify' the hash.
	"""
	hash = md5.new()

	for uri in uris:
		if not type(uri) in types.StringTypes:
			if hasattr(uri, "iteritems") and type(uri) != types.DictType:
				hash.update(pprint.pformat(dict(uri)))
			else:
				try: value = str(uri)
				except: value = repr(uri)
				hash.update(value)
		elif is_downloadable_uri(uri):
			hash.update(canonical(uri, keep_fragment = True))
		elif type(uri) == types.UnicodeType:
			hash.update(uri.encode('utf-8'))
		else:
			hash.update(uri)

	return	hash.hexdigest()

def extension(uri, default = None):
	"""Return the file extension of a URI's path"""
	if not path:
		return	default

	path = urlparse.urlparse(uri)[2]
	if not path:
		return	default

	base = os.path.basename(path)
	if not base:
		return	default

	dotx = base.rfind('.')
	if dotx == -1:
		return	default

	return	base[dotx + 1:]

if __name__ == '__main__':
	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--uri",
		default = "",
		dest = "uri",
		help = "URI to download")
	parser.add_option(
		"", "--html",
		action = "store_true",
		default = False,
		dest = "html",
		help = "Treat as an HTML document")
	parser.add_option(
		"", "--min-retry",
		type = "int",
		default = config["min_retry"],
		dest = "min_retry",
		help = "use cache within this period",
	)
	parser.add_option(
		"", "--max-retry",
		type = "int",
		default = config["max_retry"],
		dest = "max_retry",
		help = "always reload after this time",
	)
	parser.add_option(
		"", "--retries",
		type = "int",
		default = config["retries"],
		dest = "retries",
		help = "# of times to attempt to reload on failure",
	)
	parser.add_option(
		"", "--no-tidy",
		action = "store_true",
		default = False,
		dest = "no_tidy",
		help = "Don't use TIDY to fix up HTML content",
	)
	parser.add_option(
		"", "--verbose",
		action = "store_true",
		default = False,
		dest = "verbose",
		help = "Verbose logging",
	)
	parser.add_option(
		"", "--username",
		default = "",
		dest = "username",
		help = "Username for authentication"
	)
	parser.add_option(
		"", "--password",
		default = "",
		dest = "password",
		help = "Password for authentication"
	)

	(options, args) = parser.parse_args()

	if not options.uri:
		print "--uri is required\n"
		parser.print_help(sys.stderr)
		sys.exit(1)

	Log.verbose = options.verbose

	loader = HTMLLoader(
		uri = options.uri, 
		min_retry = options.min_retry, 
		max_retry = options.max_retry, 
		use_tidy = not options.no_tidy, 
		retries = options.retries,
	)
	if options.username:
		Authenticate.Global().Add(hostname = options.uri, username = options.username, password = options.password)

	try:
		loader.Load()

		if type(loader.GetCooked()) == types.UnicodeType:
			sys.stdout.write(loader.GetCooked().encode('utf-8'))
		elif type(loader.cooked) == types.StringType:
			sys.stdout.write(loader.GetCooked())
		else:
			sys.stdout.write(loader.GetRaw())

##		Log(
##			headers = loader.GetHeaders(),
##			len = len(loader.GetRaw()),
##		)
	except Unavailable:
		Log("could not download", status = loader.GetStatus(), reason = loader.GetReason())

