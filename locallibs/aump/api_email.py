#
#   api_email.py
#
#   David Janes
#   2009.01.27
#
#	Copyright 2008 David Janes
#
#	Interface to e-mail interfaces (POP3 now, IMAP4 later if needed)
#

import sys
import os
import re
import urllib
import types
import pprint
import types
import socket
import poplib
import email

import bm_text
import bm_cfg
import bm_extract
import bm_api
from bm_log import Log

ctype_re = '.*(?P<ctype>text/plain|text/html).*'
ctype_rex = re.compile(ctype_re)

head_re = """(.*?)(<\s*/\s*head\s*>|<\s*body)"""
head_rex = re.compile(head_re, re.I|re.MULTILINE|re.DOTALL)

meta_re = """<meta[^>]*>"""
meta_rex = re.compile(meta_re, re.I|re.MULTILINE|re.DOTALL)

charset_re = ";\s*charset=(?P<charset>[-a-zA-Z_0-9]+)"
charset_rex = re.compile(charset_re)

scrub_preview_re = re.compile("""<img[^>]*"snap_com_shot_link_icon"[^>]*>""")
scrub_preview_rex = re.compile(scrub_preview_re, re.I|re.VERBOSE|re.DOTALL|re.MULTILINE)

body_re = """<\s*body[^>]*>\s*(?P<body>.*?)\s*<\s*/\s*body\s*>"""
body_rex = re.compile(body_re, re.I|re.MULTILINE|re.DOTALL)

js_on_re = """
	(?P<start>
		<[^>]*
		\s+
	)
	(?P<middle>
		on[a-z]*\s*=\s*
			(?P<quote>['"])
			[^>]*?
			(?P=quote)
	)
	(?P<end>
		[^>]*
		>
	)
"""
js_on_rex = re.compile(js_on_re, re.I|re.VERBOSE|re.DOTALL|re.MULTILINE)


class POP3(bm_api.APIBase):
	_p = None
	_indicies = None

	username = None
	password = None

	text = True
	html = True
	as_is = True
	attachments = False
	header = True

	@apply
	def authenticate():
		def fset(self, service_name):
			d = bm_cfg.cfg.get(service_name)
			if not d:
				Log("warning - authentication service was not found: don't be surprised by an exception soon", service_name = service_name)
				return

			self.username = bm_extract.as_string(d, 'username')
			self.password = bm_extract.as_string(d, 'password')

		return property(**locals())

	def IterItems(self):
		self.Produced()

		self._Connect()
		self._Load()

		for index in self._indicies or []:
			yield self._GetMessage(index)

	def _Connect(self):
		assert(self.username)
		assert(self.password)

		self._p = poplib.POP3(host = "agwego.net")

		r = self._p.user(self.username)
		Log("POP3 command", command = "user", result = r, verbose = True, username = self.username)

		r = self._p.pass_(self.password)
		Log("POP3 command", command = "pass", result = r, verbose = True, password = "*" * len(self.password))

	def _Load(self):
		r_list = self._p.list()
		Log("POP3 command", command = "list", result = r_list, verbose = True)

		if len(r_list) < 2:
			return

		r_response, r_items = r_list[0], r_list[1]
		if not r_response.startswith("+OK"):
			return

		self._indicies = []
		for item in r_items:
			parts = item.split()
			if len(parts) != 2:
				continue

			item_index, item_size = parts
			self._indicies.append(item_index)

	def _GetMessage(self, item_index):
		r_msg = self._p.retr(item_index)
		r_msg_response, r_msg_body, r_rest = r_msg

		Log("POP3 command", command = "retr", result = r_msg_response, verbose = True)

		#
		#	This is the data that can be returned
		#
		msg_text = None
		msg_html = None
		attachments = []

		#
		#	Parse the message, convert to a sequence of parts
		#
		msg_obj = email.message_from_string("\n".join(r_msg_body))

		if msg_obj.is_multipart():
			msg_parts = list(msg_obj.walk())
		else:
			msg_parts = [ msg_obj, ]

		#
		#	Process each part
		#
		for msg_part in msg_parts:
			ctype = self._ExtractContentTypeFromPart(msg_part)

			filename = msg_part.get_filename()
			if filename:
				if self.attachments:
					attachments.append("".join(email.Iterators.body_line_iterator(msg_part, True)))
			elif ctype in [ 'text/plain', ]:
				msg_text = self._ExtractText(msg_part)
			elif ctype in [ 'text/html', ]:
				msg_html = self._ExtractHTML(msg_part, msg_obj)
			else:
				Log("unrecognized ctype", ctype = ctype, verbose = True)

		#
		#	Compose the result
		#
		msgd = {}

		#
		#	The text
		#
		if self.AtomLike():
			if msg_html:
				msgd['content'] = msg_html

				if msg_text:
					msgd['summary'] = bm_text.unicode2html(msg_text, p = True)

			elif msg_text:
				msgd['content'] = bm_text.unicode2html(msg_text, p = True)

			subject = msg_obj.get('subject')
			if subject:
				msgd['title'] = subject

			msg_id = msg_obj.get('message-id')
			if msg_id:
				msgd['id'] = msg_id.lstrip('<').rstrip('>')
		else:
			if msg_text:
				msgd['email:text'] = msg_text

			if msg_html:
				msgd['email:html'] = msg_html

		#
		#	The header
		#
		for key, value in msg_obj.items():
			if value:
				msgd['email:%s' % key.lower()] = value

		return	msgd
		Log("found", msg_text = msg_text, msg_html = msg_html)

	def _ExtractContentTypeFromPart(self, msg_obj):
		"""Return the Content-Type of the message, if it's text/html or text/plain"""

		ctype_value = msg_obj.get_content_type()

		ctype_match = ctype_rex.match(ctype_value)
		if ctype_match:
			return	ctype_match.group('ctype')
		
		return None

	def _ExtractCharsetFromHTML(self, body):
		head_match = head_rex.match(body)
		if head_match:
			body = head_match.group(0)

		for meta_match in meta_rex.finditer(body):
			meta = meta_match.group(0)

			charset_match = charset_rex.search(meta)
			if charset_match:
				return	charset_match.group('charset')

		return	None

	def _ExtractText(self, msg_obj):
		result = []

		for line in email.Iterators.body_line_iterator(msg_obj, True):
			result.append(line.rstrip('\n'))

		while result and result[-1] == "":
			result = result[:-1]

		return	"\n".join(result)

	def _ExtractHTML(self, msg_obj, msg_original):
		html = "".join(email.Iterators.body_line_iterator(msg_obj, True))
		html = bm_text.tounicode(html, [ msg_obj.get_charset(), self._ExtractCharsetFromHTML(html), ])
		html = self.ScrubHTML(html)

		#
		#	Per-mailer post processing
		#
		mailer = msg_original.get('X-Mailer') or ""
		mid = msg_original.get('Message-ID') or ""
		ua = msg_original.get('User-Agent') or ""

		if mailer.find('Outlook Express') > -1:
			html = self.ScrubHTMLOutlookExpress(html)
		elif mailer.find('Outlook Express') > -1:
			html = self.ScrubHTMLOutlookExpress(html)
		elif mid.find('mail.gmail.com') > -1:
			html = self.ScrubHTMLGMail(html)
		elif ua.find('Mozilla Thunderbord') > -1:
			html = self.ScrubHTMLThunderbird(html)
		elif ua.find('Microsoft-Entourage') > -1:
			html = self.ScrubHTMLEntourage(html)

		return	html

	def ScrubHTML(self, body):
		#
		#	weird preview crap
		#
		body = scrub_preview_rex.sub("", body)

		#
		#	javascript in links
		#
		count = 0
		while count < 10:
			count += 1
			
			js_on_match = js_on_rex.search(body)
			if not js_on_match:
				break

			body = js_on_rex.sub("\g<start> \g<end>", body)

		#
		#	Find only the body... Do we need to deal with BASE here?
		#
		body_match = body_rex.search(body)
		if body_match:
			return	body_match.group('body')

		return	body

	def ScrubHTMLOutlookExpress(self, body):
		body = bm_text.snip_between_tags(body, "div", replace_inner = None, replace_start = "<p>", replace_end = "</p>")
		body = bm_text.snip_between(body, 
			start_re = re.escape('<font face="Arial" size="2">'), 
			end_re = re.escape('</font>'), 
			replace_inner = None, replace_start = "", replace_end = "")
		return	body

	def ScrubHTMLOutlook(self, body):
		return	body

	def ScrubHTMLEntourage(self, body):
		return	body

	def ScrubHTMLGMail(self, body):
		#
		#	Scrub preamble postamble (i.e. On xxx so-and-so wrote:)
		#
		scrub_re = '<div>\s*<span class="gmail_quote">.*?</span>\s*' + re.escape(self.cfg_snip_html) + '\s*</div>'
		scrub_rex = re.compile(scrub_re, re.I|re.MULTILINE|re.DOTALL)

		body = scrub_rex.sub('', body)

		#
		#	GMail doesn't use proper blockquote
		#
		count = 0
		while body.find("""style="margin-left: 40px;">""") != -1 and count < 5:
			count += 1
			body = bm_text.snip_between(
				body, 
				start_re = """<(p|div) style="margin-left: 40px;">""",
				end_re = "</(p|div)>",
				replace_inner = None,
				replace_start = "<blockquote><p>",
				replace_end = "</p></blockquote>",
			)

		return	body

	def ScrubHTMLThunderbord(self, body):
		return	body

	def ExtractContentType(self, msg_obj):
		"""Return the Content-Type of the message, if it's text/html or text/plain"""

		ctype_value = msg_obj.get_content_type()

		ctype_match = ctype_rex.match(ctype_value)
		if ctype_match:
			return	ctype_match.group('ctype')
		
		return None

	def ExtractCharsetFromHTML(self, body):
		head_match = head_rex.match(body)
		if head_match:
			body = head_match.group(0)

		for meta_match in meta_rex.finditer(body):
			meta = meta_match.group(0)

			charset_match = charset_rex.search(meta)
			if charset_match:
				return	charset_match.group('charset')

		return	None
if __name__ == '__main__':
	bm_cfg.cfg.initialize()
	Log.verbose = True

	p = POP3(authenticate = "agwego-net")
	for item in p.items:
		pprint.pprint(item)
