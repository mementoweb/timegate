from urlparse import urlparse
import time
from datetime import datetime
from datetime import timedelta
from dateutil import parser as dateparser
from dateutil.tz import tzutc

import logging
from lxml import etree
import StringIO
from errors.timegateerrors import HandlerError
from core.handler import Handler

from core.timegate_utils import date_str

__author__ = "Robert Sanderson, Harihar Shankar, Yorick Chollet"


def iso_to_dt(date):

    seq = (int(date[:4]), int(date[5:7]), int(date[8:10]), int(date[11:13]),
           int(date[14:16]), int(date[17:19]), 0, 1, -1)
    return date_str(datetime.fromtimestamp(time.mktime(time.struct_time(seq)), tzutc()))


class WikiaHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

        self.hosts = [
                    'www.wowwiki.com',
                    'en.memory-alpha.org',
                    'wiki.ffxiclopedia.org',
                    'www.jedipedia.de'
        ]

    def get_memento(self, req_url, dt):
        p = urlparse(req_url)
        host = p[1]
        upath = p[2]

        if host.find('.wikia.com') == -1 and not host in self.hosts:
            return

        (pref, title) = upath.rsplit('/', 1)
        if pref:
            # look for /wiki
            pref = pref.replace('/wiki', '')
        
        changes = []
        defaultProtocol = "http://"

        dtfmstr = "%Y%m%d%H%M%S"

        dt_del = timedelta(seconds=1)
        dt_next = dt + dt_del
        dt_next = dt_next.strftime(dtfmstr)
        dt = dt.strftime(dtfmstr)

        url_list = []

        # url for getting the memento, prev
        mem_prev = "%s%s/api.php?format=xml&action=query&prop=revisions&rvprop=timestamp|ids|user&rvlimit=2&redirects=1&titles=%s&rvdir=older&rvstart=%s" % (defaultProtocol, host, title, dt)
        url_list.append('mem_prev')

        # url for next
        if dt_next:
            next = "%s%s/api.php?format=xml&action=query&prop=revisions&rvprop=timestamp|ids|user&rvlimit=2&redirects=1&titles=%s&rvdir=newer&rvstart=%s" % (defaultProtocol, host, title, dt)
            url_list.append('next')

        # url for last
        last = "%s%s/api.php?format=xml&action=query&prop=revisions&rvprop=timestamp|ids|user&rvlimit=1&redirects=1&titles=%s" % (defaultProtocol, host, title)
        url_list.append('last')

        # url for first
        first = "%s%s/api.php?format=xml&action=query&prop=revisions&rvprop=timestamp|ids|user&rvlimit=1&redirects=1&rvdir=newer&titles=%s" % (defaultProtocol, host, title)
        url_list.append('first')


        #url = url % (title, dt)
        base = "%s%s%s/index.php?title=%s&oldid=" % \
               (defaultProtocol, host, pref, title)
        dtobj = None

        hdrs = {}
        hdrs['Host'] = host

        for url in url_list:
            
            dom = self.get_xml(vars()[url], headers=hdrs)
            revs = dom.xpath('//rev')
            for r in revs:
                dt = r.attrib['timestamp']
                dtobj = dateparser.parse(r.attrib['timestamp'])
                changes.append((base + r.attrib['revid'], dt))

        return changes

    def get_all_mementos(self, req_url):

        # http://www.wowwiki.com/Cloth_armor              --> /api.php
        # http://dragonage.wikia.com/wiki/Morrigan        --> /api.php
        # http://memory-alpha.org/en/wiki/Fraggle_Rock    --> /en/api.php

        p = urlparse(req_url)
        host = p[1]
        upath = p[2]

        if host.find('.wikia.com') == -1 and not host in self.hosts:
            return
        
        (pref, title) = upath.rsplit('/', 1)
        if pref:
            # look for /wiki
            pref = pref.replace('/wiki', '')
        
        url = "http://%s%s/api.php?format=xml&action=query&prop=revisions&meta=siteinfo&rvprop=timestamp|ids&rvlimit=500&redirects=1&titles=%s" % (host, pref, title)

        changes = []
        base = "http://%s%s/index.php?oldid=" % (host, pref)

        headers = {}
        # headers['Host'] = host
        dom = self.get_xml(url, headers=headers)
        while dom is not None:
            revs = dom.xpath('//rev')
            for r in revs:
                dtstr = iso_to_dt(r.attrib['timestamp'])
                changes.append((base + r.attrib['revid'], dtstr))
            cont = dom.xpath('/api/query-continue/revisions/@rvstartid')
            if cont:
                dom = self.get_xml(url + "&rvstartid=" + cont[0], headers=headers)
            else:
                dom = None
        return changes

    def get_xml(self, uri, html=False, headers=None):

        page = self.request(uri, headers=headers)
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