#!/usr/bin/env python
import sys, os, random, time

def setup_environment():
	pathname = os.path.dirname(sys.argv[0])
	sys.path.append(os.path.abspath(pathname))
	sys.path.append(os.path.normpath(os.path.join(os.path.abspath(pathname), '../../')))
	# setup Django environment
	import settings # your settings module
	from django.core import management
	management.setup_environ(settings)

setup_environment()
from newscredit_store.crawler.models import FeedPage

def main():
  """main loop"""
  while True:
    qs = FeedPage.objects.get_due_pages()
    if qs.count() < 1:
      #if nothing in the queue, sleep a minute
      time.sleep(60)
    else:
      feed_page = random.choice(qs)
      feed_page.fetch()

main()