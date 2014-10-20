__author__ = 'Yorick Chollet'

import requests
import logging
from errors.handlererror import HandlerError

from conf.constants import PROXIES

#TODO defeine what is imported where


class Handler:

    # List of regex strings for the original resources that the handler manages
    resources = []
    # Boolean indicating if the handler can only request one Memento at a time
    singleonly = False

    # Disables all 'requests' module event logs that are at least not WARNINGS
    logging.getLogger('requests').setLevel(logging.WARNING)


    def __init__(self):
        raise NotImplementedError

    def getone(self, uri_r, datetime):
        """
        Requests one Memento for a resource and a datetime

        :param uri_r: the generic URI of the resource
        :param datetime: Optional datetime to target specific Mementos as a dateutil object
        :return: 2-Array of tuples (URI, Datetime) where Datetime = None for the
        original resource generic URI.
        """
        raise NotImplementedError

    def getall(self, uri_r):
        """
        Requests the mementos for a resource.

        :param uri_r: the generic URI of the resource
        :return: Array of tuples (URI, Datetime) where Datetime = None for the
        original resource generic URI.
        """
        raise NotImplementedError


    def request(self, resource, host="", **kwargs):
        """
        Handler helper function. Requests the resource at host.
        :param host: The hostname of the API
        :param resource: The original resource path
        :return: A requests response object
        Raises HandlerError if the requests fails to access the API
        """

        uri = host + resource

        logging.info("Sending API request for %s, params=%s" % (uri, kwargs))
        try:
            req = requests.get(uri, **kwargs)
        except Exception as e:
            raise HandlerError("Cannot request version server (%s): %s" % (uri, e.message))

        if req is None:
            raise HandlerError("Error requesting version server (%s)" % uri)
        return req
