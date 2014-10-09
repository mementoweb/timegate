from urlparse import urlparse

from dateutil import parser as dateparser

import importlib
#TODO organise imports
from conf.constants import HTTPRE, WWWRE, DATEFMT
from conf.constants import URI_PARTS as URI
from conf.constants import HTTP_STATUS as HTTP
from errors.urierror import URIRequestError
from errors.dateerror import DateRequestError
from errors.timegateerror import TimegateError
from errors.handlererror import HandlerError
import time
from datetime import timedelta
import glob
import inspect
import re

__author__ = 'Yorick Chollet'

debug = False



# TODO define if trycatch needed for badly-implemented handlers
# Builds the mapper from URI regular expression to handler class
mapper = []
extpath = 'core/extensions/'
# Finds every python files in the extensions folder and imports it
filelist = glob.glob(extpath+"*.py")
for fn in filelist:
    basen = fn[len(extpath):-3]
    modulepath = extpath.replace('/', '.')+basen
    module = importlib.import_module(modulepath)
    # Finds all python classnames within the file
    modulemembers = inspect.getmembers(module, inspect.isclass)
    for (name, path) in modulemembers:
        # If the class was not imported, extract the classname
        if str(path) == (modulepath + '.' + name):
            classname = name
            # Get the python class object from the classname and module
            handlername = getattr(module, classname)
            # Extract all URI regular expressions that the handlers manages
            handler = handlername()
            for regex in handler.resourcebase:
                # Compiles the regex and maps it to the handler python class
                mapper.append((re.compile(regex), handlername))


def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # The best Memento is the closest in time.
    best = closest

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
            timemap = handler.get(uri_r, accept_datetime)
            (uri, mementos) = processresponse(timemap)
            if uri:
                original = uri
            else:
                original = uri_r
            memento = best(mementos, accept_datetime)
            return found_response(memento, original, start_response)
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

    return parsed.geturl()


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


def found_response(memento, uri_r, start_response):
    """
    Returns the best Memento requested by the user
    :param memento:
    :param start_response:
    :return:
    """

    #TODO encoding response as utf8

    status = 302
    headers = [
        ('Date', time.strftime(DATEFMT, time.gmtime())),
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', memento.encode('utf8')),
        ('Link', '<%s>; rel="original"' % uri_r.encode('utf8'))
    ] # TODO put all normal headers in conf.constants
    body = []
    start_response(HTTP[status], headers)
    return body


def loadhandler(uri):
    """
    Loads the handler for the requested URI if it exists.
    :param uri:
    :return:
    """

    #TODO define if FIRST/ALL...
    for (regex, handler) in mapper:
        if bool(regex.match(uri)):
            return handler()

    raise URIRequestError('Cannot find any handler for %s' % uri, 404)


def closest(timemap, accept_datetime):
    """
    Finds the chronologically closest memento
    :param timemap:
    :param accept_datetime: the time object
    :return:
    """
    #TODO max

    delta = timedelta.max
    memento = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dateparser.parse(dt))
        if diff < delta:
            memento = url
            delta = diff

    return memento


def processresponse(hresponse):
    """
    Controls the response from the Handler
    :param hresponse:
    :return:
    """
    mementos = []
    try:
        for (url, dt) in hresponse:
            url_r = None
            parsed_url = urlparse(url).geturl()
            if dt:
                parsed_date = dateparser.parse(dt).strftime(DATEFMT)
                mementos.append((parsed_url, parsed_date))
            else:
                #(url, None) represents the original resource
                url_r = parsed_url

        return (url_r, mementos)

    except Exception as e:
        raise HandlerError('Bad response from Handler: %s' % e.message ,304)