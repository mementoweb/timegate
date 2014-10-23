import tgutils

__author__ = 'Yorick Chollet'

import requests
import logging
from errors.handlererror import HandlerError

#TODO defeine what is imported where


class Handler:

    # List of regex strings for the original resources that the handler manages
    resources = []
    # Boolean indicating if the handler can only request one Memento at a time
    singleonly = False

    # Disables all 'requests' module event logs that are at least not WARNINGS
    logging.getLogger('requests').setLevel(logging.DEBUG)


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


def validate_response(handler_response):
    """
    Controls and parses the response from the Handler. Also extracts URI-R if provided
    as a tuple with the form (URI, None) in the list.
    :param handler_response: Either None, a tuple (URI, date) or a list of (URI, date)
    where one tuple can have 'None' date to indicate that this URI is the original resource's.
    :return: A tuple (URI-R, Mementos) where Mementos is a (URI, date)-list of
    all Mementos. In the response, and all URIs/dates are strings and are valid.
    """

    # Input check
    if not handler_response:
        raise HandlerError('Handler response Empty.', 404)
    elif isinstance(handler_response, tuple):
        handler_response = [handler_response]
    elif not (isinstance(handler_response, list) and
                  isinstance(handler_response[0], tuple)):
        raise HandlerError('handler_response must be either None, 2-Tuple or 2-Tuple array', 503)

    # Output variables
    mementos = []
    url_r = None

    try:
        for (url, date) in handler_response:
            valid_urlstr = tgutils.validate_uristr(url)
            if date:
                # TODO sorting
                valid_datestr = tgutils.validate_datestr(date, strict=False)
                mementos.append((valid_urlstr, valid_datestr))
            else:
                #(url, None) represents the original resource
                url_r = valid_urlstr
    except Exception as e:
        raise HandlerError('Bad response from Handler:'
                           'response must be either None, (url, date)-Tuple or'
                           ' (url, date)-Tuple array, where '
                           'url, date are with standards formats  %s'
                           % e.message, 503)

    if not mementos:
        raise HandlerError('Handler response does not contain any memento for the requested resource.', 404)

    return (url_r, mementos)