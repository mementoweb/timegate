"""
WebCitation proxy
"""

import StringIO
import urllib2
import cookielib
from errors.timegateerrors import HandlerError

from lxml import etree

from core.handler import Handler

__author__ = "Robert Sanderson, Yorick Chollet"


class WebHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

    def get_all_mementos(self, requri):
        cj = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(opener)

        if requri == 'http://lanlsource.lanl.gov/hello':
            wcurl = 'http://webcitation.org/5jq247bmx'
        elif requri == 'http://lanlsource.lanl.gov/pics/picoftheday.png':
            wcurl = 'http://webcitation.org/5jq24MRo3'
        elif requri == 'http://odusource.cs.odu.edu/pics/picoftheday.png':
            wcurl = 'http://webcitation.org/5k9j4oXPw'
        elif not requri.endswith('html') and not requri.endswith('htm'):
            return []
        else:
            wcurl = 'http://webcitation.org/query.php?url=' + requri

        # txheaders = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
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
