__author__ = 'Yorick Chollet'

import requests
import logging
from operator import itemgetter

import tgutils
from errors.timegateerror import HandlerError

from conf.constants import MAX_TM_SIZE, API_TIME_OUT


class Handler:

    # Disables all 'requests' module event logs that are at least not WARNINGS
    logging.getLogger('requests').setLevel(logging.WARNING)


    def __init__(self):
        # List of regex strings for the original resources that the handler manages
        self.resources = []
        self.base = None

    # def getone(self, uri_r, datetime):
    #     """
    #     Requests one Memento for a resource and a datetime
    #
    #     :param uri_r: the generic URI of the resource
    #     :param datetime: Optional datetime to target specific Mementos as a dateutil object
    #     :return: 2-Array of tuples (URI, Datetime) where Datetime = None for the
    #     original resource generic URI.
    #     """
    #     raise NotImplementedError
    #
    # def getall(self, uri_r):
    #     """
    #     Requests the mementos for a resource.
    #
    #     :param uri_r: the generic URI of the resource
    #     :return: Array of tuples (URI, Datetime) where Datetime = None for the
    #     original resource generic URI.
    #     """
    #     raise NotImplementedError


    def request(self, resource, timeout=API_TIME_OUT, **kwargs):
        """
        Handler helper function. Requests the resource at host.
        :param host: The hostname of the API
        :param resource: The original resource path
        :return: A requests response object
        Raises HandlerError if the requests fails to access the API
        """
        uri = resource

        # Request logging for debug purposes.
        try:
            logging.info("Sending API request for %s?%s" % (
                uri, '&'.join(map(lambda(k, v): '%s=%s' % (k, v),
                                                kwargs['params'].items()))))
        except Exception as e:
            pass # Key errors on 'params'

        try:
            req = requests.get(uri, timeout=timeout, **kwargs)
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
    :return: A tuple (URI-R, Mementos) where Mementos is a sorted (URI_str, date_obj)-list of
    all Mementos. In the response, and all URIs/dates are valid.
    """

    # Input check
    if not handler_response:
        raise HandlerError('Not Found: Handler response Empty.', 404)
    elif isinstance(handler_response, tuple):
        handler_response = [handler_response]
    elif not (isinstance(handler_response, list) and
                  isinstance(handler_response[0], tuple)):
        raise HandlerError('handler_response must be either None, 2-Tuple or 2-Tuple array', 502)
    elif len(handler_response) > MAX_TM_SIZE:
        raise HandlerError('Handler response too big and unprocessable.', 502)

    # Output variables
    mementos = []
    url_r = None

    try:
        for (url, date) in handler_response:
            valid_urlstr = tgutils.validate_uristr(url)
            if date:
                valid_date = tgutils.validate_date(date, strict=False)
                mementos.append((valid_urlstr, valid_date))
            else:
                #(url, None) represents the original resource
                url_r = valid_urlstr
    except Exception as e:
        raise HandlerError('Bad response from Handler:'
                           'response must be either None, (url, date)-Tuple or'
                           ' (url, date)-Tuple array, where '
                           'url, date are with standards formats  %s'
                           % e.message, 502)

    if not mementos:
        raise HandlerError('Handler response does not contain any memento for the requested resource.', 404)
    else:
        # Sort by datetime
        sorted_list = sorted(mementos, key=itemgetter(1))


    return (url_r, sorted_list)