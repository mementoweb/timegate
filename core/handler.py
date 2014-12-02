from core import tgutils

__author__ = 'Yorick Chollet'

import logging
from operator import itemgetter

import requests

from errors.timegateerrors import HandlerError
from core.constants import TM_MAX_SIZE, API_TIME_OUT


class Handler:

    # Disables all 'requests' module event logs that are at least not WARNINGS
    logging.getLogger('requests').setLevel(logging.WARNING)

    def __init__(self):
        pass
        # assert not (hasattr(self, 'get_memento') or hasattr(self, 'get_all_mementos'))

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
            # Key errors on 'params'
            logging.info("Sending API request for %s" % uri)

        try:
            req = requests.get(uri, timeout=timeout, **kwargs)
        except Exception as e:
            logging.error("Cannot request version server (%s): %s" % (uri, e.message))
            raise HandlerError("Cannot request version server.", 502)

        if req is None:
            logging.error("Error requesting version server (%s): %s" % uri)
            raise HandlerError("Error requesting version server.", 502)
        return req


def validate_response(handler_response):
    """
    Controls and parses the response from the Handler.
    as a tuple with the form (URI, None) in the list.
    :param handler_response: Either None, a tuple (URI, date) or a list of (URI, date)
    where one tuple can have 'None' date to indicate that this URI is the original resource's.
    :return: A sorted (URI_str, date_obj)-list of
    all Mementos. In the response, and all URIs/dates are valid.
    """

    # Input check
    if not handler_response:
        raise HandlerError('Not Found: Handler response Empty.', 404)
    elif isinstance(handler_response, tuple):
        handler_response = [handler_response]
    elif not (isinstance(handler_response, list) and
                  isinstance(handler_response[0], tuple)):
        logging.error('Bad response from Handler:'
                        'Not a tuple nor tuple array')
        raise HandlerError('Bad handler response.', 503)
    elif len(handler_response) > TM_MAX_SIZE:
        logging.warning('Bad response from Handler:'
                        'TimeMap (%d  greater than max %d)' %
                        (len(handler_response), TM_MAX_SIZE))
        raise HandlerError('Handler response too big and unprocessable.', 502)

    # Output variables
    mementos = []

    try:
        for (url, date) in handler_response:
            valid_urlstr = tgutils.validate_uristr(url)
            valid_date = tgutils.validate_date(date, strict=False)
            mementos.append((valid_urlstr, valid_date))
    except Exception as e:
        logging.error('Bad response from Handler:'
                        'response must be either None, tuple(url, date) or'
                        ' [tuple(url, date)]. Where '
                        'url, date are with standards formats  %s')
        raise HandlerError('Bad response from Handler:', 503)

    if not mementos:
        raise HandlerError('Handler response does not contain any memento for the requested resource.', 404)
    else:
        # Sort by datetime
        sorted_list = sorted(mementos, key=itemgetter(1))


    return sorted_list