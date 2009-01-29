#
#	bm_oauth.py
#
#	David Janes
#	2009.01.21
#
#	OAuth indentification functions and helpers
#

import time
import sys
import hashlib
import urllib
import urllib2
import urlparse
import hmac
import base64
import random
import webbrowser
import pprint

import bm_uri
import bm_cfg
import bm_extract

from bm_log import Log

try:
	import json
except ImportError:
	import simplejson as json

class OAuth(bm_uri.Auth):
	def __init__(self, service_name = None, cfg = None, api_uri = None, **ad):
		bm_uri.Auth.__init__(self, service_name = service_name, cfg = cfg, api_uri = api_uri)

		self.oauth_signature_method = u'HMAC-SHA1'
		self.oauth_version = u'1.0'

		self.oauth_consumer_key = ''
		self.oauth_consumer_secret = ''

		self.oauth_token_secret = u''
		self.oauth_token = u''

		self.oauth_token_url = '';
		self.oauth_access_token_url = '';
		self.oauth_authorization_url = '';

		self.oauth_uri = ''
		self.oauth_api_root = ''

		for key, value in ad.iteritems():
			if key.startswith("oauth_") and hasattr(self, key):
				setattr(self, key, value)
				
		if self.service_name:
			self.LoadCfg()

	def Dump(self):
		Log(
			oauth_signature_method = self.oauth_signature_method,
			oauth_version = self.oauth_version,
			oauth_consumer_key = self.oauth_consumer_key,
			oauth_consumer_secret = self.oauth_consumer_secret,
			oauth_token_secret = self.oauth_token_secret,
			oauth_token = self.oauth_token,
			oauth_token_url = self.oauth_token_url,
			oauth_access_token_url = self.oauth_access_token_url,
			oauth_authorization_url = self.oauth_authorization_url,
			oauth_api_root = self.oauth_api_root,
		)

	def LoadCfg(self):
		"""Load a service by name from the CFG"""

		cfg = self.cfg or bm_cfg.cfg

		if not self.service_name:
			raise	ValueError("service_name is required during initialization")

		d = cfg.get(self.service_name)
		if not d:
			Log("did not find service in bm_cfg", name = self.service_name)
			return

		for key, value in d.iteritems():
			if key.startswith("oauth_") and hasattr(self, key) and not getattr(self, key):
				setattr(self, key, value)
				
		#
		#	Handle requests using OAuth
		#
		api_uri = d.get("api_uri")
		if api_uri:
			if not self.oauth_token_secret or not self.oauth_token:
				Log("not registering for bm_uri.Authenticate because service is not fully OAuthorized", service = self.service_name)

			bm_uri.Authenticate.Global().Add(api_uri, self)

	def SaveCfg(self, cfg = None):
		cfg = cfg or bm_cfg.cfg

		if not self.service_name:
			d = {}
		else:
			d = cfg.get(self.service_name)
			if not d:
				d = {}

		for key in dir(self):
			if key.startswith("oauth_"):
				d[key] = getattr(self, key)

		d[bm_cfg.IS_CHANGED] = True

	def GetAuthorizeURI(self):
		"""This will return	the URI that you need to go to to authorize your application"""

		self.oauth_uri = ''
		self.oauth_token_secret = u''
		self.oauth_token = u''

		self._RequestToken()
		self._AuthorizeToken()

		self.SaveCfg()

	def GetExchangeTokens(self):
		self._ExchangeToken()

		self.oauth_uri = ''
		self.SaveCfg()

	def Test(self):
		self._RequestData()

	def _RequestToken(self):
		Log('REQUEST TOKEN')
		paramd = {
			'oauth_consumer_key': self.oauth_consumer_key,
			'oauth_version': self.oauth_version,
			'oauth_timestamp': u''+str(int(time.time())),
			'oauth_nonce': u''+self._GenerateNonce(),
			'oauth_signature_method': self.oauth_signature_method
		}
		response = self.parse_response(self.GET(self.oauth_token_url, paramd))

		self.oauth_token = response['oauth_token']
		self.oauth_token_secret = response['oauth_token_secret']

	def _AuthorizeToken(self):
		Log('AUTHORIZE TOKEN')
		paramd = {
			'oauth_consumer_key': self.oauth_consumer_key,
			'oauth_version': self.oauth_version,
			'oauth_timestamp': u''+str(int(time.time())),
			'oauth_nonce': u''+self._GenerateNonce(),
			'oauth_signature_method': self.oauth_signature_method,
			'oauth_token': self.oauth_token,
			'oauth_callback': 'http://localhost',
		}

		self.oauth_uri = \
			self.oauth_authorization_url + \
			'?' + urllib.urlencode(paramd) + \
			'&oauth_signature=' + self._GenerateSignature(self.oauth_authorization_url, paramd)

	def _ExchangeToken(self):
		Log('EXCHANGE TOKEN')
		paramd = {
			'oauth_consumer_key': self.oauth_consumer_key,
			'oauth_version': self.oauth_version,
			'oauth_timestamp': u''+str(int(time.time())),
			'oauth_nonce': u''+self._GenerateNonce(),
			'oauth_signature_method': self.oauth_signature_method,
			'oauth_token': self.oauth_token
		}
		response = self.parse_response(self.GET(self.oauth_access_token_url, paramd))

		self.oauth_token = response['oauth_token']
		self.oauth_token = urllib.unquote(self.oauth_token)

		self.oauth_token_secret = response['oauth_token_secret']
		self.oauth_token_secret = urllib.unquote(self.oauth_token_secret)

		Log(
			"HERE:B",
			oauth_token = self.oauth_token,
			oauth_token_secret = self.oauth_token_secret,
		)

	def _RequestData(self):
		Log('REQUEST DATA')
		paramd = {
			'oauth_consumer_key': self.oauth_consumer_key,
			'oauth_version': self.oauth_version,
			'oauth_timestamp': u''+str(int(time.time())),
			'oauth_nonce': u''+self._GenerateNonce(),
			'oauth_signature_method': self.oauth_signature_method,
			'oauth_token': self.oauth_token,
			'format': 'json'
		}
		result = self.GET('https://fireeagle.yahooapis.com/api/0.1/user.json', paramd)
		jd = json.loads(result)
		pprint.pprint(jd, width = 1)

	def _GenerateSignature(self, url, paramd):
		for p in paramd:
			paramd[p] = urllib.quote(paramd[p], '')
				
		paramd_keys = paramd.keys()
		paramd_keys.sort()
	
		sig = ''
		for key in paramd_keys:
			sig += key +'='+ paramd[key] +'&'

		sig = 'GET&' + urllib.quote(url, '') + '&' + urllib.quote(sig[:-1])

		key = urllib.quote(self.oauth_consumer_secret) + '&' + str(self.oauth_token_secret)
		m = hmac.new(key, sig, hashlib.sha1)
		m = base64.b64encode(m.digest())

		return	urllib.quote(m)

	def _GenerateNonce(self):
		return	hashlib.md5(str(int(time.time())) + str(random.random())).hexdigest()
	
	def parse_response(self, response):
		response = response.split('&')
		return	{
			'oauth_token': response[0].split('=')[1],
			'oauth_token_secret': response[1].split('=')[1]
		}
	
	def GET(self, url, paramd):
		loader = bm_uri.URILoader(
			url + '?' + urllib.urlencode(paramd) + 
			'&oauth_signature=' + self._GenerateSignature(url, paramd),
			authenticate = bm_uri.Authenticate(),
		)

		Log(url = url, uri = 
			url + '?' + urllib.urlencode(paramd) + 
			'&oauth_signature=' + self._GenerateSignature(url, paramd),
		)

		try:
			return	loader.Load()
		except bm_uri.DownloaderError:
			Log(exception = True, data = loader.GetRaw())

	def BuildRequest(self, loader):
		"""See bm_uri.Auth.BuildRequest"""

		#
		#	Keys needed for OAuth
		#
		paramd = {
			'oauth_consumer_key': self.oauth_consumer_key,
			'oauth_version': self.oauth_version,
			'oauth_timestamp': u''+str(int(time.time())),
			'oauth_nonce': u''+self._GenerateNonce(),
			'oauth_signature_method': self.oauth_signature_method,
			'oauth_token': self.oauth_token,
		}

		#
		#	Unwind all the arguments from the URI, then add to paramd
		#
		urip = urlparse.urlparse(loader.uri)

		uri_base = "%s://%s%s" % ( urip.scheme, urip.netloc, urip.path )
		uri_params = urip.query.split("&")
		
		for p in uri_params:
			parts = p.split('=', 1)
			if len(parts) == 2:
				paramd[parts[0]] = parts[1]
				
		#
		#	Make a new downloading URL
		#
		new_uri = uri_base + \
			'?' + urllib.urlencode(paramd) + \
			'&oauth_signature=' + self._GenerateSignature(uri_base, paramd)

		Log(oauth_uri = new_uri, verbose = True)

		#
		#	And download....
		#
		if loader.method == "POST":
			self.request = urllib2.Request(new_uri, data = urllib.urlencode(d))
		else:
			self.request = urllib2.Request(new_uri)
			


if __name__ == '__main__':
	bm_cfg.cfg.initialize()

	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--service",
		default = None,
		dest = "service_name",
		help = "Service to load from the CFG (e.g. fireeagle)",
	)
	parser.add_option(
		"", "--host",
		default = "",
		dest = "host",
		help = "Hostname where the API resides (e.g. www.example.com)",
	)
	parser.add_option(
		"", "--authenticate",
		action = "store_true",
		default = False,
		dest = "authenticate",
		help = "Authenticate your application - will open in browser",
	)
	parser.add_option(
		"", "--exchange",
		action = "store_true",
		default = False,
		dest = "exchange",
		help = "Exchange authentication token - call after you confirm authentication",
	)
	parser.add_option(
		"", "--test",
		action = "store_true",
		default = False,
		dest = "test",
		help = "Test something",
	)
	parser.add_option(
		"", "--verbose",
		action = "store_true",
		default = False,
		dest = "verbose",
		help = "Verbose logging",
	)
	parser.add_option(
		"", "--dump",
		action = "store_true",
		default = False,
		dest = "vdump",
		help = "Dump oauth information",
	)

	(options, args) = parser.parse_args()

	Log.verbose = options.verbose

	oauth = OAuth(service_name = options.service_name)

	if options.host:
		oauth.LoadHost(options.host)

	if options.service_name:
		oauth.LoadCfg()

	if options.authenticate:
		oauth.GetAuthorizeURI()
		print oauth.oauth_uri
		## webbrowser.open(oauth.oauth_uri)
	elif options.exchange:
		oauth.GetExchangeTokens()
	elif options.test:
		oauth.Test()
	else:
		print >> sys.stderr, "%s: one of --exchange, --authenticate should be chosen" % sys.argv[0]

	if options.service_name:
		bm_cfg.cfg.Save()

	oauth.Dump()

