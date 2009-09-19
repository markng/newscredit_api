#
#   hnews.py
#   Ref: http://valueaddednews.org/technical/techspec
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

import microformat
import hcard
import relprinciples
#import hrights
from microformat import Log

class MicroformatHNews(microformat.Microformat):
    def __init__(self, **args):
        microformat.Microformat.__init__(self, root_name = "hnews",
            uf_name = "hNews", root_type = "class",
            collect_ids = True, **args)

        self.CollectClassCall('source-org', self.DoSourceOrg)
        self.CollectClassCall('dateline', self.DoDateline)
        #self.CollectClassCall('hrights', hrights.MicroformatHRights(page_uri = self.page_uri, parent = self))
        self.CollectRelReparse('principles', relprinciples.MicroformatRelPrinciples(page_uri = self.page_uri, parent = self))
        self.DeclareRepeatingName('principles')


        self.CollectClassModifier('geo')
        self.CollectClassText('latitude', text_type = microformat.TT_STRING)
        self.CollectClassText('longitude', text_type = microformat.TT_STRING)

    def Spawn(self):
        mf = MicroformatHNews(page_uri = self.page_uri)
        mf.data = self.data
        mf.intermediates = self.intermediates
        mf.root_element = self.root_element
        self.Reset()

        return  mf

    #
    #   Source Orgs must be hCards
    #
    def DoSourceOrg(self, name, element):
        if "vcard" in element.getAttribute("class").split():
            self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri), name)

    #
    #   Datelines can be plain text or hCards. Published and updated attributes
    #   will be picked up by hAtom
    #
    def DoDateline(self, name, element):
        if "vcard" in element.getAttribute("class").split():
            self.DoCollectClassReparse(name, element, hcard.MicroformatHCard(page_uri = self.page_uri), name)
        else:
            self.AddResult(name, element, self.GetText(element))

if __name__ == '__main__':
    import microformat
    # microformat.debug = 1

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
    # Log.verbose = options.verbose

    parser = MicroformatHNews(page_uri = options.page_uri)
    parser.PragmaCLI(args)

    for resultd in parser.Iterate():
        pprint.pprint(resultd, width = 1)

