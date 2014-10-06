from wsgi import application

__author__ = 'Yorick Chollet'

import unittest  # Python unit test structure

from webtest import TestApp  # WSGI application tester

server = TestApp(application.application)


class TestServerSequence(unittest.TestCase):

    def test_server_up(self):
        response = server.get('/', status=200)


def suite():
        st = unittest.TestSuite()
        st.addTest(unittest.makeSuite(TestServerSequence))
        return st
