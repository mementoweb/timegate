# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""WebCitation proxy."""

from __future__ import absolute_import, print_function

import logging
import StringIO
import urllib2

from lxml import etree

import cookielib
from timegate.errors import HandlerError
from timegate.handler import Handler


class WebCiteHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        cj = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

    def get_all_mementos(self, requri):

        if requri == 'http://lanlsource.lanl.gov/hello':
            wcurl = 'http://webcitation.org/5jq247bmx'
        elif requri == 'http://lanlsource.lanl.gov/pics/picoftheday.png':
            wcurl = 'http://webcitation.org/5jq24MRo3'
        elif requri == 'http://odusource.cs.odu.edu/pics/picoftheday.png':
            wcurl = 'http://webcitation.org/5k9j4oXPw'
        else:
            return self.get_from_xml(requri)  # Cleaner but much slower
            # wcurl = 'http://webcitation.org/query.php?url=' + requri  # Fast
            # screen scraping

        txheaders = {}

        try:
            req = urllib2.Request(wcurl, None, txheaders)
            fh = urllib2.urlopen(req)
            fh.close()

            req = urllib2.Request('http://webcitation.org/topframe.php')
            fh = urllib2.urlopen(req)
            data = fh.read()
            fh.close()
        except Exception as e:
            raise HandlerError('Cannot request page', 404)

        changes = []

        try:
            parser = etree.HTMLParser()
            dom = etree.parse(StringIO.StringIO(data), parser)
        except:
            raise HandlerError('Cannot parse HTML')

        opts = dom.xpath('//select[@name="id"]/option')
        for o in opts:
            fid = o.attrib['value']
            date = o.text
            if date.find('(failed)') > -1:
                continue

            changes.append(('http://webcitation.org/query?id=' + fid, date))

        return changes

    def get_from_xml(self, requri):
        api_request = 'http://webcitation.org/query.php?returnxml=1&url=' + requri
        xml = self.request(api_request, timeout=120)

        try:
            parser = etree.XMLParser(recover=True)  # Parses bad XML
            dom = etree.parse(StringIO.StringIO(str(xml.text)), parser)
        except Exception as e:
            logging.error('Cannot parse XML: ' + str(e))
            raise HandlerError('Cannot parse XML', 404)

        results = []
        succes = dom.xpath("//result[@status='success']")
        for s in succes:
            url = s.find('webcite_url').text
            date = s.find('timestamp').text

            results.append((url, date))

        return results
