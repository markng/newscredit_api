#!/usr/bin/env python
import sys, os, random, time
def setup_environment():
	pathname = os.path.dirname(sys.argv[0])
	sys.path.append(os.path.normpath(os.path.join(os.path.abspath(pathname), '../../')))
	sys.path.append(os.path.abspath(pathname))
	# setup Django environment
	import settings # your settings module
	from django.core import management
	management.setup_environ(settings)

setup_environment()
from crawler.models import FeedPage
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
  def __str__(self):
    """docstring for __str__"""
    return self.name
  def run(self):
    """fetch it"""
    try:
      self.name = page.id
      self.page.fetch()
      self.page.save()
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
  #become_daemon()
  threads = []
  while True:
    reap(threads)
    if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
      pages = get_pages()
      for page in pages:
        if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
          thread = FetchIt(page)
          threads.append(thread)
          thread.start()
    time.sleep(60)
  