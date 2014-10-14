from pip._vendor.requests.packages.urllib3 import request

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError


class OtherHandler(Handler):

    def __init__(self):

        self.resources = ['http://www.an\d{1,2}.other.com/',
                          'http://www.another.com/[a-zA-Z0-9]*/']

        self.singleonly = False

    def get(self, uri, datetime):
        api_uri = 'http://127.0.0.1:9001/timemap2/'
        req = self.request(api_uri, uri)

        if not req or req.status_code == 404:
            raise HandlerError("Cannot find resource on version server.", 404)
        elif req.status_code == 200:
            assert (req.headers['content-type'].startswith('application/json'))
            json = req.json()
            uri_r = json['original_uri']
            dict_list = json['mementos']['all']
            def keys2tuple(e):
                return tuple(e.values())
            tuplelist = map(keys2tuple, dict_list)
            tuplelist.append((uri_r, None))
            return tuplelist

        else:
            raise HandlerError("Unknown API response.", 503)
