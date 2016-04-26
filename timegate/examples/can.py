# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Canadian archive proxy."""

from __future__ import absolute_import, print_function

import logging
import re
import StringIO

from lxml import etree

from timegate.errors import HandlerError
from timegate.handler import Handler


class CanHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.baseuri = "http://www.collectionscanada.gc.ca/webarchives/*/"
        self.dtre = re.compile(
            "http://www.collectionscanada.gc.ca/webarchives/(\d+)/")

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
        page = self.request(uri)
        try:
            page_data = page.content
            if not html:
                parser = etree.XMLParser(recover=True)
            else:
                parser = etree.HTMLParser(recover=True)
            return etree.parse(StringIO.StringIO(page_data), parser)
        except Exception as e:
            logging.error("Cannot parse XML/HTML from %s" % uri)
            raise HandlerError("Couldn't parse data from %s" % uri, 404)
