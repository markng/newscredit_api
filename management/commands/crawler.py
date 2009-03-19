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
from django.utils.daemonize import become_daemon
from django.conf import settings
from threading import Thread
from pprint import pprint

class FetchIt(Thread):
  """fetch a page"""
  def __init__(self, page):
    super(FetchIt, self).__init__()
    self.page = page
    self.status = False
  def run(self):
    """fetch it"""
    try:
      self.page.fetch()
      self.status = True
    except Exception, e:
      self.status = e

def get_pages():
  return(FeedPage.objects.get_due_pages())

def reap(threads):
  # clear list of dead threads
  for thread in threads:
    if not thread.isAlive():
      threads.remove(thread)

if __name__ == '__main__':
  threads = []
  while True:
    reap(threads)
    if threads <= settings.MAXIMUM_CRAWLER_THREADS:
      pages = get_pages()
      for page in pages:
        if threads <= settings.MAXIMUM_CRAWLER_THREADS:
          thread = FetchIt(page)
          threads.append(thread)
          thread.start()
    time.sleep(60)
  