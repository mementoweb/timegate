from pip._vendor.requests.packages.urllib3 import request

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError

#TODO define what needs to be imported in superclass, so what will be needed in
#Handlers


class FooHandler(Handler):


    def __init__(self):

        self.resourcebase = ['http://www.foo.bar/*']

        self.singleonly = True



    def get(self, uri, datetime=None):
        api_uri = 'http://127.0.0.1:9001/single/'

        # Requests the API
        req = self.request(api_uri, uri)

        # Handles API Response
        if not req or req.status_code == 404:
            raise HandlerError("Cannot find resource on version server.", 404)
        elif req.status_code == 200:
            # Assume the API handles the requests correctly
            assert (req.headers['content-type'].startswith('application/json'))

            # Extract the JSON elements URI-R and (Mementos, Datetime) pair
            json = req.json()
            # Single only
            memento_josn = json['mementos']['all'][0]

            # In this example we omit URI-R. just reponds the Memento
            return tuple(memento_josn.values())

        else:
            # API response undefined.
            raise HandlerError("Unknown API response.", 503)
