# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Memento proxy for Portuguese Web Archive arquivo.pt."""

from __future__ import absolute_import, print_function

import StringIO
import logging
import re

from lxml import etree

from timegate.errors import HandlerError
from timegate.handler import Handler
from timegate.utils import get_uri_representations


def get_uri_representations(uri):
    """Needed because some API do not process the url canonization properly,
    and treat http://example.com and http://www.example.com differently.

    This function returns the list of canonical representation of a URI.
    It also appends the `http://` protocol if missing. For instance,
    *uri*='example.com' will return ['http://example.com',
    'http://www.example.com'] and *uri*='domain.example.com' will return
    ['http://domain.example.com'].

    :param uri: The uri string to make canonical.
    :return: The canonical representations of this URI.
    """
    uri_list = []

    m = re.match(r'(https?://)?(www.)?(.+)', uri)
    if not m:
        return uri_list
    http, www, netloc = m.groups()
    # domain.example.com/path/ not example.com/path/
    has_subdomain = len(netloc.split('/')[0].split('.')) > 2

    if not http:
        http = 'http://'

    if www:
        uri_list.append(http + www + netloc)
        if not has_subdomain:
            uri_list.append(http + netloc)
    else:
        www = 'www.'
        uri_list.append(http + netloc)
        if not has_subdomain:
            uri_list.append(http + www + netloc)

    return uri_list


class PoHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://arquivo.pt/wayback/wayback/xmlquery"

    def get_all_mementos(self, req_uri):
        all_mementos = []
        [all_mementos.extend(self.query(uri))
         for uri in get_uri_representations(req_uri)]
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
        """Retrieves the resource using the url, parses it as XML or HTML and
        returns the parsed dom object.

        :param uri: [str] The uri to retrieve :param headers:
        [dict(header_name: value)] optional http headers to send in the
        request :param html: [bool] optional flag to parse the response
        as HTML :return: [lxml_obj] parsed dom.

        """

        page = self.request(uri, params=params)
        try:
            page_data = page.content
            if not html:
                parser = etree.XMLParser(recover=True)
            else:
                parser = etree.HTMLParser(recover=True)
            return etree.parse(StringIO.StringIO(page_data), parser)
        except Exception:
            logging.error("Cannot parse XML/HTML from %s" % uri)
            raise HandlerError("Couldn't parse data from %s" % uri, 404)
