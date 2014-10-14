from pip._vendor.requests.packages.urllib3 import request

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError

class FooHandler(Handler):


    def __init__(self):

        self.resources = ['http://www.foo.bar/']
        self.singleonly = True


    # This example requires the datetime
    def get(self, uri, datetime):
        api_uri = 'http://127.0.0.1:9001/single/'
        req = self.request(api_uri, uri)
        if not req or req.status_code == 404:
            raise HandlerError("Cannot find resource on version server.", 404)
        elif req.status_code == 200:
            assert (req.headers['content-type'].startswith('application/json'))

            json = req.json()
            # Single only
            memento_josn = json['mementos']['all'][0]

            # In this example we omit URI-R and just return the Memento
            return tuple(memento_josn.values())

        else:
            # API response undefined.
            raise HandlerError("Unknown API response.", 503)
