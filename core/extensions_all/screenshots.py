__author__ = "Robert Sanderson, Yorick Chollet"

import logging
from lxml import etree
import StringIO
from errors.timegateerrors import HandlerError
from core.handler import Handler


class SsHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://www.screenshots.com/"

    def get_all_mementos(self, req_url):
        # implement the changes list for this particular proxy

        if req_url.startswith('http://'):
            req_url = req_url[7:]
        elif req_url.startswith('https://'):
            req_url = req_url[8:]

        changes = []

        if req_url[-1] == '/':
            req_url = req_url[:-1]
        if req_url.find('/') > -1:
            return changes
        
        uri = self.baseuri + req_url + '/'
        dom = self.get_xml(uri, html=True)
        if dom:
            rlist = dom.xpath('//img')
            for a in rlist:
                if 'class' in a.attrib:
                    if a.attrib['class'].startswith('sliderThumb'):
                        dtstr = a.attrib['name']
                        loc = a.attrib['longdesc']
                        dtstr += " 12:00:00 GMT"
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

