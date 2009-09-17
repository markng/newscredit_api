#!/usr/bin/env python
#
# Management script which runs the crawler daemon.
#
import random
import sys
import time

from threading import Thread

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
        print u'Fetching page %s' % self.page.url
        try:
            self.name = self.page.id
            self.page.fetch()
            self.page.save()
            self.status = True
        except Exception, e:
            self.status = e

def get_pages():
    from crawler.models import FeedPage
    return(FeedPage.objects.get_due_pages())

def reap(threads):
    # clear list of dead threads
    for thread in threads:
        if not thread.isAlive():
            threads.remove(thread)

def run_daemon():
    #become_daemon()
    threads = []
    while True:
        reap(threads)
        if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
            pages = None
            pages = get_pages()
            for page in pages:
                if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
                    thread = FetchIt(page)
                    threads.append(thread)
                    thread.start()
        time.sleep(60)

from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.utils.daemonize import become_daemon

class Command(NoArgsCommand):
    help = "Runs the Crawler daemon until terminated by Ctrl-C"

    def handle_noargs(self, **options):
        try:
            run_daemon()
        except KeyboardInterrupt:
            print "bye bye"
            sys.exit(0)