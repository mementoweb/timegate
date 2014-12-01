"""
Canadian archive proxy.
"""
__author__ = "Robert Sanderson, Yorick Chollet"

from core.handler import Handler

import logging
from lxml import etree
import StringIO
from errors.timegateerrors import HandlerError
import re

class CanHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://www.collectionscanada.gc.ca/webarchives/*/"
        self.dtre = re.compile("http://www.collectionscanada.gc.ca/webarchives/(\d+)/")

    def get_all_mementos(self, req_url):
        iauri = self.baseuri + req_url
        dom = self.get_xml(iauri, html=True)

        alist = dom.xpath('//div[@class="inner-content"]//a')
        if not alist:
            return []

        changes = []
        for a in alist:
            if not 'name' in a.attrib:
                uri = a.attrib['href']
                match = self.dtre.match(uri)
                if bool(match):
                    dtstr = match.groups()[0]
                    changes.append((uri, dtstr))
        return changes

    def get_xml(self, uri, html=False):
        """
        Retrieves the resource using the url, parses it as XML or HTML
        and returns the parsed dom object.
        :param uri: [str] The uri to retrieve
        :param headers: [dict(header_name: value)] optional http headers to send in the request
        :param html: [bool] optional flag to parse the response as HTML
        :return: [lxml_obj] parsed dom.
        """

        page = self.request(uri)
        page_data = page.content
        try:
            if not html:
                parser = etree.XMLParser(recover=True)
            else:
                parser = etree.HTMLParser(recover=True)
            return etree.parse(StringIO.StringIO(page_data), parser)
        except Exception as e:
            logging.error("Cannot parse XML/HTML from %s" % uri)
            raise HandlerError("Couldn't parse data from %s" % uri)