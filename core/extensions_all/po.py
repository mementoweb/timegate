# Memento proxy for Portuguese Web Archive arquivo.pt

import logging
from lxml import etree
import StringIO
from errors.timegateerrors import HandlerError
from core.handler import Handler
from core.timegate_utils import get_uri_representations

__author__ = "aalsum, Yorick Chollet"


class PoHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://arquivo.pt/wayback/wayback/xmlquery"

    def get_all_mementos(self, req_uri):
        all_mementos = []
        [all_mementos.extend(self.query(uri)) for uri in get_uri_representations(req_uri)]
        return all_mementos

    def query(self, resource):
        # implement the changes list for this particular proxy
        param = {'url': resource,
                 'type': 'urlquery'}

        changes = []

        uri = self.baseuri + resource
        dom = self.get_xml(uri, params=param)
        if dom:
            rlist = dom.xpath('/wayback/results/result')
            for a in rlist:
                dtstr = a.xpath('./capturedate/text()')[0]
                url = a.xpath('./url/text()')[0]
                loc = "http://arquivo.pt/wayback/wayback/%s/%s" % (dtstr, url)

                dtstr += " GMT"
                changes.append((loc, dtstr))

        return changes

    def get_xml(self, uri, params=None, html=False):
        """
        Retrieves the resource using the url, parses it as XML or HTML
        and returns the parsed dom object.
        :param uri: [str] The uri to retrieve
        :param headers: [dict(header_name: value)] optional http headers to send in the request
        :param html: [bool] optional flag to parse the response as HTML
        :return: [lxml_obj] parsed dom.
        """

        page = self.request(uri, params=params)
        page_data = page.content
        try:
            if not html:
                parser = etree.XMLParser(recover=True)
            else:
                parser = etree.HTMLParser(recover=True)
            return etree.parse(StringIO.StringIO(page_data), parser)
        except Exception:
            logging.error("Cannot parse XML/HTML from %s" % uri)
            raise HandlerError("Couldn't parse data from %s" % uri)






