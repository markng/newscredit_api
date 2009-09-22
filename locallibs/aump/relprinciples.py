#
#   relprinciples.py
#
#   Matt Harris
#   Tokofu
#   2009.09.18
#

import sys

import os
import os.path
import pprint
import types
import re
import xml.dom.minidom
import xml.dom
import urllib
import urlparse

from bm_log import Log

import microformat
import hcard
from microformat import Log

class MicroformatRelPrinciples(microformat.Microformat):
    def __init__(self, **args):
        microformat.Microformat.__init__(self, root_name = "principles",
            uf_name = "rel-principles", root_type = "rel", **args)

        # self.CollectClassText('rating', text_type = microformat.TT_ABBR)
        # self.CollectClassText('best', text_type = microformat.TT_ABBR)
        # self.CollectClassText('worst', text_type = microformat.TT_ABBR)

        self.CollectRelAttribute('principles', 'href')
        self.CollectRelText('principles', as_name = 'principles', 
            text_type = microformat.TT_STRING)
        self.DeclareURI('authority')

        self.DeclareTitle("principles")

    def Spawn(self):
        mf = MicroformatRelPrinciples(page_uri = self.page_uri)
        mf.data = self.data
        mf.intermediates = self.intermediates
        mf.root_element = self.root_element
        self.Reset()

        return  mf

    def AddResult(self, name, element, text):
        if name == "principles":
            uri = text
            if self.page_uri:
                uri = urlparse.urljoin(self.page_uri, uri)

            text = self.GetText(element)
            microformat.Microformat.AddResult(self, "uri", element, uri)

        microformat.Microformat.AddResult(self, name, element, text)

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
    parser.add_option(
        "", "--verbose",
        default = False,
        action = "store_true",
        dest = "verbose",
        help = "print a lot about what is happening",
    )

    (options, args) = parser.parse_args()
    Log.verbose = options.verbose

    parser = MicroformatRelPrincples(page_uri = options.page_uri)
    parser.PragmaCLI(args)

    for resultd in parser.Iterate():
        pprint.pprint(resultd, width = 1)

