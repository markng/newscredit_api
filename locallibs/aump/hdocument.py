#
#	hdocument.py
#
#	David Janes
#	BlogMatrix
#	2006.09.08
#

import sys

import os
import pprint
import types
import copy
import re
import xml.dom.minidom
import xml.dom
import urlparse

import bm_uri
import bm_text

import microformat
import hcard
import reltag

from bm_log import Log

feedfinder = None
try:
	import feedfinder

	class OurGatekeeper(feedfinder.URLGatekeeper):
		def get(self, url, check=True):
			try:
				uri_loader = bm_uri.HTMLLoader(url)
				uri_loader.Load()
			except:
				Log(url = url, exception = True)
				return	''

			return	uri_loader.GetRaw() or ''

	feedfinder._gatekeeper = OurGatekeeper()
except ImportError:
	pass

title_re = """<\s*title\s*>\s*(.*?)\s*</\s*title\s*>"""
title_rex = re.compile(title_re, re.I|re.MULTILINE|re.DOTALL)

h_re = """<\s*(h[1-6])\s*[^>]*>\s*(.*?)\s*</\s*h[1-6]\s*>"""
h_rex = re.compile(h_re, re.I|re.MULTILINE|re.DOTALL)

a_re = """<\s*a(\s+[^>]*?)\s*>(?P<text>.*?)</a>"""
a_rex = re.compile(a_re, re.I|re.MULTILINE|re.DOTALL)

img_re = """<\s*img(\s+[^>]*?)\s*>"""
img_rex = re.compile(img_re, re.I|re.MULTILINE|re.DOTALL)

attr_re = """\s([a-z0-9]*)\s*=\s*["']([^'"]*)["']"""
attr_rex = re.compile(attr_re, re.I|re.MULTILINE|re.DOTALL)

class MicroformatDocument(microformat.Microformat):
	def __init__(self, **args):
		for key in [ 'do_feed', 'do_h', 'do_img', 'do_a', 'do_title', ]:
			try:
				value = args.pop(key)
			except KeyError:
				value = True

			setattr(self, key, value)

		microformat.Microformat.__init__(self, root_name = "html", uf_name = "document", **args)

	def Spawn(self):
		mf = MicroformatDocument(page_uri = self.page_uri, parent = self)
		mf.data = self.data
		mf.intermediates = self.intermediates
		mf.root_element = self.root_element
		self.Reset()

		return	mf

	def Feed(self, *av, **ad):
		try:
			microformat.Microformat.Feed(self, *av, **ad)
		except:
			Log("ignoring XML parsing failure", exception = True)
			self.dom = None

	def Iterate(self):
		uri_loader = bm_uri.HTMLLoader(self.page_uri)
		uri_loader.Load()

		cooked = uri_loader.GetRaw()

		#
		#	need for further parsing
		#
		base_uri = self.page_uri

		if self.dom:
			base_elements = self.dom.getElementsByTagName("base")
			if base_elements:
				base_element = base_elements[0]
				href = base_element.getAttribute("href")
				if href:
					base_uri = urlparse.urljoin(self.page_uri, href)
		else:
			base_uri = self.page_uri

			## ... XXX ... needs to be finished ...

		#
		#	images
		#
		if self.do_h:
			self.DoH(base_uri, cooked)

		if self.do_title:
			self.DoTitle(base_uri, cooked)

		if self.do_feed:
			self.DoFeed(base_uri, cooked)

		if self.do_img:
			self.DoIMG(base_uri, cooked)

		if self.do_a:
			self.DoA(base_uri, cooked)

		#
		#	Simulating the normal Iterate...
		#
		self.PutData('@uf', self.uf_name)
		self.PutData('@html', '')
		self.PutData('@uri', self.page_uri)

		spawned = self.Spawn()
		resultd = spawned.data
		resultd.microformat = spawned
		resultd.data = None

		yield	resultd

	def DoTitle(self, base_uri, cooked):
		for title_match in title_rex.finditer(cooked):
			title = title_match.group(1)
			title = bm_text.scrub_html(title)

			self.PutData("@title", title)
			self.PutData("title", title)

	def DoH(self, base_uri, cooked):
		for h_match in h_rex.finditer(cooked):
			htag = h_match.group(1).lower()

			hvalue = h_match.group(2)
			hvalue = bm_text.scrub_html(hvalue)

			if not hvalue:
				continue

			self.PutData("@title", hvalue)
			self.PutData(htag, hvalue)

	def DoFeed(self, base_uri, cooked):
		feedds = []
		if feedfinder:
			feed_uris = feedfinder.feeds(self.page_uri)
			for feed_uri in feed_uris:
				feedd = {
					"@uf" : "feed",
					"@link" : feed_uri,
					"@title" : "feed",
					"src" : feed_uri,
				}

				feedds.append(feedd)

		self.PutData("feed", feedds)

	def DoIMG(self, base_uri, cooked):
		imageds = []

		if not self.dom:
			image_uris = {}

			for img_match in img_rex.finditer(cooked):
				img_element = img_match.group(1)

				width = None
				height = None
				src_uri = None
				title = None

				for attr_match in attr_rex.finditer(img_element):
					name = attr_match.group(1).lower()
					value = attr_match.group(2)

					if name == "src":
						src_uri = value
					elif name == "width":
						try: width = int(value)
						except: pass
					elif name == "height":
						try: height = int(value)
						except: pass
					elif name == "title":
						title = value

				if width and width < 16:
					src_uri = None
				if height and height < 16:
					src_uri = None

				if not src_uri:
					continue

				src_uri = urlparse.urljoin(self.page_uri, src_uri)

				if image_uris.get(src_uri):
					continue

				image_uris[src_uri] = 1

				title = title or os.path.basename(src_uri)

				imaged = {
					"@uf" : "html",
					"@link" : src_uri,
					"@title" : title,
					"src" : src_uri,
					"title" : title,
				}

				if width and height:
					imaged["height"] = height
					imaged["width"] = width

				imageds.append(imaged)

		else:
			image_uris = {}

			for img_element in self.dom.getElementsByTagName("img"):
				width = img_element.getAttribute("width")
				if width:
					try:
						if int(width) < 16:
							continue
					except:
						pass

				height = img_element.getAttribute("height")
				if height:
					try:
						if int(height) < 16:
							continue
					except:
						pass


				src_uri = img_element.getAttribute("src")
				if not src_uri:
					continue

				src_uri = urlparse.urljoin(self.page_uri, src_uri)

				if image_uris.get(src_uri):
					continue

				image_uris[src_uri] = 1

				title = img_element.getAttribute("title") or os.path.basename(src_uri)

				imaged = {
					"@uf" : "html",
					"@uri" : src_uri,
					"@title" : title,
					"src" : src_uri,
					"title" : title,
				}

				if width and height:
					imaged["height"] = height
					imaged["width"] = width

				imageds.append(imaged)

		self.PutData("image", imageds)

	def DoA(self, base_uri, cooked):
		ads = []

		if not self.dom:
			a_uris = {}

			for a_match in a_rex.finditer(cooked):
				a_element = a_match.group(1)
				text = a_match.group('text').strip()

				rel = None
				type = None
				href = None
				title = None

				for attr_match in attr_rex.finditer(a_element):
					name = attr_match.group(1).lower()
					value = attr_match.group(2)

					if name == "href":
						href = value
					elif name == "rel":
						rel = value
					elif name == "type":
						type = value
					elif name == "title":
						title = value

				if not href:
					continue

				href = urlparse.urljoin(self.page_uri, href)

				if a_uris.get(href):
					continue

				a_uris[href] = 1

				title = title or os.path.basename(href)

				ad = {
					"@uf" : "html",
					"@link" : href,
					"href" : href,
				}

				if text: ad["text"] = text
				if type: ad["type"] = type
				if rel: ad["rel"] = rel
				if title:
					ad["title"] = title
					ad["@title"] = title

				ads.append(ad)
		else:
			a_uris = {}

			for a_element in self.dom.getElementsByTagName("a"):
				href = a_element.getAttribute("href")
				if not href:
					continue

				rel = a_element.getAttribute("rel")
				type = a_element.getAttribute("type")
				text = self.GetText(a_element)
				text = " ".join(text.strip().split())

				href = urlparse.urljoin(self.page_uri, href)

				if a_uris.get(href):
					continue

				a_uris[href] = 1

				title = a_element.getAttribute("title") or os.path.basename(href)

				ad = {
					"@uf" : "html",
					"@uri" : href,
					"@title" : title,
					"href" : href,
				}

				if text: ad["text"] = text
				if type: ad["type"] = type
				if rel: ad["rel"] = rel
				if title:
					ad["title"] = title
					ad["@title"] = title

				ads.append(ad)

		self.PutData("a", ads)

if __name__ == '__main__':
	import microformat
	microformat.debug = 1

	from optparse import OptionParser

	parser = OptionParser()
	parser.add_option(
		"", "--uri",
		default = "",
		dest = "page_uri",
		help = "The URI of the page being processed")

	(options, args) = parser.parse_args()

	parser = MicroformatDocument(page_uri = options.page_uri)
	parser.PragmaCLI(args)

	for resultd in parser.Iterate():
		pprint.pprint(resultd, width = 1)

