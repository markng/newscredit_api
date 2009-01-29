#
#	bm_wsgi.py
#
#	David Janes
#	2008.12.07
#

import cgi
import bm_text

import wsgiref.handlers
import wsgiref.headers

from bm_log import Log

class SimpleWrapper:
	def __init__(self, environ, start_response, content_type = 'text/html', charset = 'utf-8', encoding = None):
		self.environ = environ
		self.start_response = start_response
		self.headers = wsgiref.headers.Headers([])
		self.paramd = cgi.parse_qs(self.environ.get('QUERY_STRING', ''))
		self.content_type = content_type
		self.charset = charset
		self.encoding = encoding
		self.code = '200 OK'

	def NormalStart(self):
		self.headers.add_header('Content-Type', self.content_type, charset = self.charset)

		if self.encoding:
			self.headers.add_header('Content-Encoding', self.encoding)

		self.start_response(self.code, self.headers.items())

	def RunCGI(cls):
		wsgiref.handlers.CGIHandler().run(cls)

	def __iter__(self):
		first = True

		try:
			self.CustomizeSetup()

			for content in self.CustomizeContent():
				if first:
					self.NormalStart()
					first = False

				yield	bm_text.toutf8(content)
		except:
			if first:
				self.headers.add_header('Content-type', 'text/plain')
				self.start_response('500 Error', self.headers.items())

				yield	Log(exception = True)

	def CustomizeSetup(self):
		pass
		
	def CustomizeContent(self):
		raise	NotImplementedError
		
	RunCGI = classmethod(RunCGI)


