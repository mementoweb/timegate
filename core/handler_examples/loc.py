import StringIO
import logging

import re
from lxml import etree

from core.handler_baseclass import Handler


__author__ = "Robert Sanderson, Yorick Chollet"


class LocHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

        self.datere = re.compile('http://webarchive.loc.gov/[a-zA-Z0-9]+/([0-9]+)/.+')
        self.colls = [
            'lcwa0001',
            'lcwa0002',
            'lcwa0003',
            'lcwa0004',
            'lcwa0005',
            'lcwa0006',
            'lcwa0007',
            'lcwa0008',
            'lcwa0009',
            'lcwa0010',
            'lcwa0011',
            'lcwa0012',
            'lcwa0013',
            'lcwa0014',
            'lcwa0015',
            'lcwa0016',
            'lcwa0017',
            'lcwa0018',
            'lcwa0019',
            'lcwa0020',
            'lcwa0029',
            'lcwa0031',
            'lcwa0032',
            'lcwa0033',
            'lcwa0037'
        ]

    def get_all_mementos(self, requri):
        changes = []

        for c in self.colls:
            iauri = "http://webarchives.loc.gov/%s/*/%s" % (c, requri)

            try:
                req = self.request(iauri)
                data = req.content
            except Exception as e:
                continue

            try:
                parser = etree.HTMLParser(recover=True)
                dom = etree.parse(StringIO.StringIO(data), parser)
            except Exception as e:
                logging.error("Exception parsing data in loc handler: %s" % e.message)
                continue

            alist = dom.xpath('//a')

            for a in alist:
                loc = a.attrib.get('href', '')
                if loc.startswith('http://webarchive.loc.gov/%s/' % c):

                    # extract time from link
                    m = self.datere.match(loc)
                    if m and a.tail:
                        datestr = m.groups()[0]
                        changes.append((loc, datestr))
        return changes