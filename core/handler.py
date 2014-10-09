__author__ = 'Yorick Chollet'

import requests
import dateutil
from errors.handlererror import HandlerError

from conf.constants import PROXIES


class Handler:

    resourcebase = None
    # TODO decide if either here or PER REGEX
    singleonly = False

    def __init__(self):
        raise NotImplementedError

    def get(self, uri_r, datetime=None):
        """
        Requests the mementos for a resource.

        :param uri_r: the generic URI of the resource
        :param datetime: Optional datetime to target specific Mementos as a dateutil object
        :return: Array of tuples (URI, Datetime) where Datetime = None for the
        original resource generic URI.
        """
        raise NotImplementedError

    def request(self, host, resource):
        try:
            req = requests.get(host+resource)
            return req
        except Exception as e:
            raise HandlerError("Cannot request version server (%s): %s" % (host + resource, e.message))
