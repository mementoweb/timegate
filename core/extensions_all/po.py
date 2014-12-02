# Memento proxy for Portuguese Web Archive arquivo.pt

import logging
from lxml import etree
import StringIO
from errors.timegateerrors import HandlerError
from core.handler import Handler

__author__ = "aalsum, Yorick Chollet"


class PoHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://arquivo.pt/wayback/wayback/xmlquery?type=urlquery&url="

    def get_all_mementos(self, req_url, dt=None):
        # implement the changes list for this particular proxy
        param = {'url': req_url,
                 'type': 'urlquery'}

        changes = []

        uri = self.baseuri + req_url
        dom = self.get_xml(uri)
        if dom:
            rlist = dom.xpath('/wayback/results/result')
            for a in rlist:
                dtstr = a.xpath('./capturedate/text()')[0]
                url = a.xpath('./url/text()')[0]
                loc = "http://arquivo.pt/wayback/wayback/%s/%s" % (dtstr, url)

                dtstr += " GMT"
                changes.append((loc, dtstr))

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

