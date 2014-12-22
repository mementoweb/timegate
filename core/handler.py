from core import timegate_utils

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

    def request(self, resource, timeout=API_TIME_OUT, **kwargs):
        """
        Handler helper function. Requests the resource over HTTP.
        Logs the request and handles exceptions
        :param resource: The resource to get
        :param timeout: The HTTP Timeout for a single request
        :param kwargs: The keywords arguments to pass to the request method (`params`).
        :return: A requests response object
        :raises HandlerError: if the requests fails to access the API
        """
        uri = resource

        # Request logging with params
        try:
            logging.info("Sending request for %s?%s" % (
                uri, '&'.join(map(lambda(k, v): '%s=%s' % (k, v), kwargs['params'].items()))))
        except Exception:
            # Key errors on 'params'
            logging.info("Sending request for %s" % uri)

        try:
            req = requests.get(uri, timeout=timeout, **kwargs)
        except Exception as e:
            logging.error("Cannot request server (%s): %s" % (uri, e.message))
            raise HandlerError("Cannot request version server.", 502)

        if req is None:
            logging.error("Error requesting server (%s): %s" % uri)
            raise HandlerError("Error requesting version server.", 404)

        if not req:
            logging.info("Response other than 2XX: %s" % req)
            raise HandlerError("API response not 2XX", 404)
        return req


def parsed_request(handler_function, *args, **kwargs):
    """
    Retrieves, and parses the response from the Handler.
    This function is the point of entry to all handler requests
    :param handler_function: The function to call
    :param args: Arguments to :handler_function:
    :param kwargs: Keywords arguments to :handler_function:
    :return: A sorted [(URI_str, date_obj),...] list of all Mementos. In the response, and all URIs/dates are valid.
    :raise HandlerError: In case of a bad response from the handler
    """
    try:
        handler_response = handler_function(*args, **kwargs)
    except HandlerError as he:
        logging.info("Handler raised HandlerError %s" % he.message)
        raise he  # HandlerErrors have return data.
    except Exception as e:
        logging.error("Handler raised exception %s" % e.message)
        raise HandlerError("Error in Handler", 503)

    # Input check
    if not handler_response:
        raise HandlerError('Not Found: Handler response Empty.', 404)
    elif isinstance(handler_response, tuple):
        handler_response = [handler_response]
    elif not (isinstance(handler_response, list) and
                  isinstance(handler_response[0], tuple)):
        logging.error('Bad response from Handler: Not a tuple nor tuple array')
        raise HandlerError('Bad handler response.', 503)
    elif len(handler_response) > TM_MAX_SIZE:
        logging.warning('Bad response from Handler: TimeMap (%d  greater than max %d)' %
                        (len(handler_response), TM_MAX_SIZE))
        raise HandlerError('Handler response too big and unprocessable.', 502)

    valid_response = []
    try:
        for (url, date) in handler_response:
            valid_urlstr = timegate_utils.validate_uristr(url)
            valid_date = timegate_utils.validate_date(date, strict=False)
            valid_response.append((valid_urlstr, valid_date))
    except Exception as e:
        logging.error('Bad response from Handler:'
                        'response must be either None, tuple(url, date) or'
                        ' [tuple(url, date)]. Where '
                        'url, date are with standards formats  %s')
        raise HandlerError('Bad response from Handler:', 503)

    if not valid_response:
        raise HandlerError('Handler response does not contain any memento for the requested resource.', 404)
    else:
        # Sort by datetime
        sorted_list = sorted(valid_response, key=itemgetter(1))


    return sorted_list