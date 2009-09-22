#!/usr/bin/env python
#
# Management script which runs the crawler daemon.
#
import random
import sys
import time
import logging

from threading import Thread

class FetchIt(Thread):
    """fetch a page"""
    def __init__(self, page):
        super(FetchIt, self).__init__()
        self.logger = logging.getLogger(
            'crawler.FetchIt'
        )
        self.page = page
        self.status = False

    def __str__(self):
        """docstring for __str__"""
        return self.name

    def run(self):
        """fetch it"""
        try:
            self.logger.debug(u'Page ID %d' % self.page.id)
            self.name = self.page.id
            self.page.fetch()
            self.page.save()
            self.status = True
        except Exception, e:
            self.logger.error(u'Exception thrown %s' % e)
            self.status = e

def get_pages():
    from crawler.models import FeedPage
    return(FeedPage.objects.get_due_pages())

def reap(threads):
    logger.debug(u'Removing inactive threads')
    # clear list of dead threads
    for thread in threads:
        if not thread.isAlive():
            threads.remove(thread)

def run_daemon():
    #become_daemon()
    threads = []
    while True:
        logger.debug(u'Entering loop')
        reap(threads)
        if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
            logger.debug(u'Obtaining pages')
            pages = None
            pages = get_pages()
            for page in pages:
                if len(threads) <= settings.MAXIMUM_CRAWLER_THREADS:
                    logger.debug(u'Creating new thread %d',
                        len(threads))
                    thread = FetchIt(page)
                    threads.append(thread)
                    thread.start()
        logger.debug(u'Sleeping for 60 seconds')
        time.sleep(60)

from django.core.management.base import NoArgsCommand
from django.conf import settings
from django.utils.daemonize import become_daemon

logger = logging.getLogger('crawler')
if settings.LOG_LEVEL is not None:
    logger.setLevel(logging.__getattribute__(settings.LOG_LEVEL))

    # enable logging to file if requested
    if settings.LOG_TO_FILE:
        fh = logging.FileHandler("crawler.log")
        # This needs to be False to stop the FileHandler outputting to
        # stdout
        logger.propagate = False
        logger.addHandler(fh)
    else:
        # enable logging to the stdout
        ch = logging.StreamHandler()
        logger.addHandler(ch)
else:
    logger.setLevel(sys.maxint)

class Command(NoArgsCommand):
    help = "Runs the Crawler daemon until terminated by Ctrl-C"

    def handle_noargs(self, **options):
        try:
            run_daemon()
        except KeyboardInterrupt:
            print "bye bye"
            sys.exit(0)