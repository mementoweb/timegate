from urlparse import urlparse

from dateutil import parser as dateparser

import importlib

from conf.constants import HTTPRE, WWWRE, DATEFMT
from conf.constants import URI_PARTS as URI
from conf.constants import HTTP_STATUS as HTTP
from errors.urierror import URIRequestError
from errors.dateerror import DateRequestError
from errors.timegateerror import TimegateError
from errors.handlererror import HandlerError
from core.timegate import Timegate
from core.timemap import Timemap


__author__ = 'Yorick Chollet'

debug = False


def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # The best Memento is the closest.
    best = closest

    # Debug prints
    if debug:
        print("ENV: \n %s" % env)


    # Extracting requested values
    req_path = env.get("PATH_INFO", "/")
    req_datetime = env.get("HTTP_ACCEPT_DATETIME")

    # Standard Response
    status = 404
    message = "404 - Not Found \n"
    headers = [('Content-Type', 'text/html')]

    # Processing request path
    req_path = req_path.lstrip('/')
    req_type = req_path.split('/', 1)[0]

    # TimeGate Logic
    if req_type == URI['G']:
        # Processing request
        try:
            accept_datetime = dateparse(req_datetime)
            uri_r = uriparse(req_path, req_type)
            handler = loadhandler(uri_r)
            timemap = handler.get(uri_r.geturl(), accept_datetime)
            memento = best(timemap, accept_datetime)
            return response(memento, start_response)
        except TimegateError as e:
            return error_response(e.status, e.message,
                                  start_response, headers)

    # TimeMap Logic
    elif req_type == URI['T']:
        body = ["400 - Bad request. Timemap not implemented yet \n"]
        status = 400

    # TestCase Logic
    elif req_type == "test":
        body = ["server running"]
        status = 200

    else:
        message = "URI type does not match timegate or timemap"
        if debug:
            print "URI type does not match timegate or timemap"

    return error_response(status, message, start_response, headers)


def dateparse(datestr):
    try:
        date = dateparser.parse(datestr)
        return date
    except Exception as e:
        raise DateRequestError("Error on Accept-Datetime: %s "
                               "\n \n details: %s" % (datestr, e.message))


#TODO whitespaces escapes
def uriparse(pathstr, typestr):
    """
    Parses the requested URI
    :param urlstr:
    :return:
    """

    path = pathstr[len(typestr+'/'):] #removes leading timegate/

    if not path:
        raise URIRequestError("Error: Empty path")

    # Trying to fix incomplete URI
    if not bool(HTTPRE.match(path)):
        if not bool(WWWRE.match(path)):
            path = 'www.'+path
        path = 'http://'+path

    try:
        parsed = urlparse(path, scheme='http')
    except Exception as e:
        raise URIRequestError("Error: Cannot parse path: %s" % e.message)

    return parsed


def error_response(status, message, start_response, headers):
    """
    Returns an error message to the user
    :param status:
    :param message:
    :param start_response:
    :param headers:
    :return:
    """
    body = ["%s \n %s" % (status, message)]
    start_response(HTTP[status], headers)
    return body


def response(memento, start_response):
    """
    Returns the best Memento requested by the user
    :param memento:
    :param start_response:
    :return:
    """
    status = 200
    headers = []
    body = []

    start_response(HTTP[status], headers)
    return body


def loadhandler(uri):
    """
    Loads the handler for the requested URI if it exists.
    :param uri:
    :return:
    """

    #TODO modularizer ca...
    if uri.netloc == 'www.example.com':
        module = importlib.import_module('core.extensions.example')
        hanclerclss = getattr(module, 'ExampleHandler')
        handler = hanclerclss()
        return handler
    else:
        raise URIRequestError('Cannot find any handler for %s' % uri.geturl(), 404)


def closest(timemap, accept_datetime):
    """
    Finds the chronologically closest memento
    :param timemap:
    :param accept_datetime:
    :return:
    """

    #TODO IMplement
    return timemap[0]


def processresponse(hresponse):
    """
    Controls the response from the Handler
    :param hresponse:
    :return:
    """

    def tupleparser(tu):
        (url, dt) = tu
        return (urlparse(url).geturl(), dateparser.parse(dt).strftime(DATEFMT))

    # def tuplecomparator(t1, t2):
    #     if t1[1] :
    #         return -1
    #     elif :
    #         return 0
    #     else:
    #         return 1

    try:
        parsed_list = hresponse.map(tupleparser)
        # sortedlist = parsed_list.sort(tuplecomparator)
        return parsed_list
    except Exception as e:
        raise HandlerError('Bad response from Handler: %s' % e.message ,304)