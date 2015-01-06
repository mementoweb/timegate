# -*- coding: utf-8 -*-
from core import application

__author__ = 'Yorick Chollet'

import time
import unittest  # Python unit test structure

from webtest import TestApp  # WSGI application tester

from core.constants import TIMEMAP_URI_PART, TIMEGATE_URI_PART
from core.constants import DATE_FORMAT


server = TestApp(application.application)

DATEHEADER = 'Wed, 15 Oct 2014 20:40:19 GMT'

#
# class TestServerSequence(unittest.TestCase):
#
#     def test_server_up(self):
#         response = server.get('/test/', status=200)
#         assert len(response.normal_body) > 1
#
#     def test_server_tgroot_status(self):
#         response = server.get('/%s/' % TIMEGATE_URI_PART, status=400)
#
#     def test_server_tmroot_status(self):
#         response = server.get('/%s/' % TIMEMAP_URI_PART, status=400)
#
#     def test_dateOK(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         response = server.get('/%s/uri' % TIMEGATE_URI_PART, headers=ad, status=200)
#
#     def test_dateWRONG(self):
#         timestr = time.strftime("å/ンページ/ %s /הצלת", time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         response = server.get('/%s/uri' % TIMEGATE_URI_PART, headers=ad, status=400)
#
#     def test_urlOK(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         response = server.get('/%s/http://www.example.com/resource/' % TIMEGATE_URI_PART, headers=ad, status=200)
#
#     def test_urlTRUNKATED(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         response = server.get('/%s/example.com/resource' % TIMEGATE_URI_PART, headers=ad, status=200)
#
#     def test_urlINEXISTANT(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         response = server.get('/%s/http://www.wrong.url/' % TIMEGATE_URI_PART, headers=ad, status=200)
#
#     def test_urlUNSAFE(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         url = """/timegate/http://www.wrong.url/å/ンページ/  /הצלת/é/"""
#         response = server.get(url, headers=ad, status=200)
#
#     def test_urlNOSLASHR(self):
#         timestr = time.strftime(DATE_FORMAT, time.gmtime())
#         ad = {'Accept-Datetime': timestr}
#         url = """/timegatewww.wrong.url"""
#         response = server.get(url, headers=ad, status=404)

class TestServerRealSeq(unittest.TestCase):

    def test_TG_github_all_resources(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/mementoweb/timegate' % TIMEGATE_URI_PART, headers=ad, status=302)
        response = server.get('/%s/https://github.com/mementoweb/timegate/tree/master/core' % TIMEGATE_URI_PART, headers=ad, status=302)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/timegate/master/core/extension/example3.py' % TIMEGATE_URI_PART, headers=ad, status=302)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extension/example3.py' % TIMEGATE_URI_PART, headers=ad, status=302)

    def test_TM_github_all_resources(self):
        ad = {'Accept-Datetime': 'none'}
        response = server.get('/%s/https://github.com/mementoweb/timegate' % TIMEMAP_URI_PART, headers=ad, status=200)
        response = server.get('/%s/https://github.com/mementoweb/timegate/tree/master/core' % TIMEMAP_URI_PART, headers=ad, status=200)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/timegate/master/core/extension/example3.py' % TIMEMAP_URI_PART, headers=ad, status=200)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extension/example3.py' % TIMEMAP_URI_PART, headers=ad, status=200)

    def test_github_404s(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/memento2web/timegate' % TIMEMAP_URI_PART, headers=ad, status=404)
        response = server.get('/%s/https://github.com/meme/2/ntoweb/timegate/tree/master/core' % TIMEMAP_URI_PART, headers=ad, status=404)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/tim/egate/master/core/extension/example3.py' % TIMEMAP_URI_PART, headers=ad, status=404)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extension/exajmple3.py' % TIMEMAP_URI_PART, headers=ad, status=404)


    def test_github_bad_req(self):
        ad = {'Accept-Datetime': 'Today'}
        response = server.get('/%s/https://github.com/memento2web/timegate' % TIMEGATE_URI_PART, headers=ad, status=400)
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/meme/2/ntoweb/timegate/tree/master/core' % 'test', headers=ad, status=400)

    def test_wiki_ok(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/en.wikipedia.org/wiki/Palézieux' % TIMEGATE_URI_PART, headers=ad, status=302)
        response = server.get('/%s/en.wikipedia.org/wiki/Palézieux' % TIMEMAP_URI_PART, status=200)


    def test_wiki_404(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/eeen.wikipedia.org/wiki/Albert_Einstein' % TIMEGATE_URI_PART, headers=ad, status=404)
        response = server.get('/%s/en.wikipedia.org/wiki/Eiiiiinstein' % TIMEMAP_URI_PART, status=404)
        response = server.get('/%s/en.wikipedia.org/kiwi/Albert_Einstein' % TIMEMAP_URI_PART, status=404)

        # TODO add test all kinds of BS responses from handlers



def suite():
    st = unittest.TestSuite()
    st.addTest(unittest.makeSuite(TestServerRealSeq))
    return st
