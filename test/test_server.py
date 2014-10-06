import time

from application import application as serv
from conf.constants import URI_PARTS as URI


__author__ = 'Yorick Chollet'

import unittest  # Python unit test structure

from webtest import TestApp  # WSGI application tester

server = TestApp(serv)


class TestServerSequence(unittest.TestCase):

    def test_server_up(self):
        response = server.get('/test/', status=200)
        assert response.normal_body == "server running"

    def test_server_tgroot_status(self):
        response = server.get('/%s/' % URI['G'], status=400)

    def test_server_tmroot_status(self):
        response = server.get('/%s/' % URI['T'], status=400)

    # def test_server_tgroot_body(self):
    #     response = server.get('/%s/' % URI['G'])
    #     assert str.startswith(response.normal_body, URI['G'])

    def test_process_dateOK(self):
        timestr = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/' % URI['G'], headers=ad, status=200)

    def test_process_dateWRONG(self):
        timestr = "today 18:00 2012 18th October "
        ad = {'Accept-Datetime': timestr}
        response = server.get('/%s/' % URI['G'], headers=ad, status=400)

def suite():
        st = unittest.TestSuite()
        st.addTest(unittest.makeSuite(TestServerSequence))
        return st
