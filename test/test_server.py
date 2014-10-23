# -*- coding: utf-8 -*-
import time

import application
from conf.constants import TIMEMAPSTR, TIMEGATESTR
from conf.constants import DATEFMT

from test.apistub import application as apistub

__author__ = 'Yorick Chollet'

import unittest  # Python unit test structure

from webtest import TestApp  # WSGI application tester

server = TestApp(application.application)
api = TestApp(apistub)

DATEHEADER = 'Wed, 15 Oct 2014 20:40:19 GMT'


class TestServerSequence(unittest.TestCase):

    def test_server_up(self):
        response = server.get('/test/', status=200)
        assert len(response.normal_body) > 1

    def test_server_tgroot_status(self):
        response = server.get('/%s/' % TIMEGATESTR, status=400)

    def test_server_tmroot_status(self):
        response = server.get('/%s/' % TIMEMAPSTR, status=400)

    def test_dateOK(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/uri' % TIMEGATESTR, headers=ad, status=200)

    def test_dateWRONG(self):
        timestr = time.strftime("å/ンページ/ %s /הצלת", time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/uri' % TIMEGATESTR, headers=ad, status=400)

    def test_urlOK(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/http://www.example.com/resource/' % TIMEGATESTR, headers=ad, status=200)

    def test_urlTRUNKATED(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/example.com/resource' % TIMEGATESTR, headers=ad, status=200)

    def test_urlINEXISTANT(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/http://www.wrong.url/' % TIMEGATESTR, headers=ad, status=200)

    def test_urlUNSAFE(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        url = """/timegate/http://www.wrong.url/å/ンページ/  /הצלת/é/"""
        response = server.get(url, headers=ad, status=200)

    def test_urlNOSLASHR(self):
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        url = """/timegatewww.wrong.url"""
        response = server.get(url, headers=ad, status=404)

class TestServerHandlerSeq(unittest.TestCase):

    def test_stub_up(self):
        response = api.get('/test/', status=404)
        assert len(response.normal_body) > 1

    def test_flow(self):
        api = TestApp(apistub)
        timestr = time.strftime(DATEFMT, time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/timegate/example.com/', headers=ad, status=200)

class TestServerRealSeq(unittest.TestCase):

    def test_TG_github_all_resources(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/mementoweb/timegate' % TIMEGATESTR, headers=ad, status=302)
        response = server.get('/%s/https://github.com/mementoweb/timegate/tree/master/core' % TIMEGATESTR, headers=ad, status=302)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/timegate/master/core/extensions/example3.py' % TIMEGATESTR, headers=ad, status=302)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extensions/example3.py' % TIMEGATESTR, headers=ad, status=302)

    def test_TM_github_all_resources(self):
        ad = {'Accept-Datetime': 'none'}
        response = server.get('/%s/https://github.com/mementoweb/timegate' % TIMEMAPSTR, headers=ad, status=200)
        response = server.get('/%s/https://github.com/mementoweb/timegate/tree/master/core' % TIMEMAPSTR, headers=ad, status=200)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/timegate/master/core/extensions/example3.py' % TIMEMAPSTR, headers=ad, status=200)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extensions/example3.py' % TIMEMAPSTR, headers=ad, status=200)

    def test_github_404s(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/memento2web/timegate' % TIMEMAPSTR, headers=ad, status=404)
        response = server.get('/%s/https://github.com/meme/2/ntoweb/timegate/tree/master/core' % TIMEMAPSTR, headers=ad, status=404)
        response = server.get('/%s/https://raw.githubusercontent.com/mementoweb/tim/egate/master/core/extensions/example3.py' % TIMEMAPSTR, headers=ad, status=404)
        response = server.get('/%s/https://github.com/mementoweb/timegate/blob/master/core/extensions/exajmple3.py' % TIMEMAPSTR, headers=ad, status=404)


    def test_github_bad_req(self):
        ad = {'Accept-Datetime': 'Today'}
        response = server.get('/%s/https://github.com/memento2web/timegate' % TIMEGATESTR, headers=ad, status=400)
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/https://github.com/meme/2/ntoweb/timegate/tree/master/core' % 'test', headers=ad, status=400)

    def test_wiki_ok(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/en.wikipedia.org/wiki/Palézieux' % TIMEGATESTR, headers=ad, status=302)
        response = server.get('/%s/en.wikipedia.org/wiki/Palézieux' % TIMEMAPSTR, status=200)


    def test_wiki_404(self):
        ad = {'Accept-Datetime': DATEHEADER}
        response = server.get('/%s/eeen.wikipedia.org/wiki/Albert_Einstein' % TIMEGATESTR, headers=ad, status=404)
        response = server.get('/%s/en.wikipedia.org/wiki/Eiiiiinstein' % TIMEMAPSTR, status=404)
        response = server.get('/%s/en.wikipedia.org/kiwi/Albert_Einstein' % TIMEMAPSTR, status=404)

        # TODO add test all kinds of BS responses from handlers




def suite():
    st = unittest.TestSuite()
    # st.addTest(unittest.makeSuite(TestServerSequence))
    # st.addTest(unittest.makeSuite(TestServerHandlerSeq))
    st.addTest(unittest.makeSuite(TestServerRealSeq))
    return st
