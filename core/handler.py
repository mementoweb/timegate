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

    def get(self, uri_r, datetime):
        """
        Requests the mementos for a resource.

        :param uri_r: the generic URI of the resource
        :param datetime: Optional datetime to target specific Mementos as a dateutil object
        :return: Array of tuples (URI, Datetime) where Datetime = None for the
        original resource generic URI.
        """
        raise NotImplementedError

    def request(self, host, resource):
        """
        Handler helper function. Requests the resource at host.
        :param host: The hostname of the API
        :param resource: The original resource path
        :return: A requests response object
        Raises HandlerError if the requests fails to access the API
        """

        logging.info("Sending API request for %s" % host+resource)
        try:
            req = requests.get(host+resource)
            return req
        except Exception as e:
            raise HandlerError("Cannot request version server (%s): %s" % (host + resource, e.message))
