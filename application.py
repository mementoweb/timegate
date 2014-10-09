__author__ = 'Yorick Chollet'

import importlib
import inspect
import time
import re
import glob
from urlparse import urlparse
from datetime import timedelta

from dateutil import parser as dateparser

from conf.constants import HTTPRE, WWWRE, DATEFMT, URI_PARTS, HTTP_STATUS, HOST, EXTENSIONS_PATH
from errors.urierror import URIRequestError
from errors.dateerror import DateTimeError
from errors.timegateerror import TimegateError
from errors.handlererror import HandlerError


# TODO define if trycatch needed for badly-implemented handlers
# Builds the mapper from URI regular expression to handler class
try:
    tgate_mapper = []
    tmap_mapper = []
    # Finds every python files in the extensions folder and imports it
    files = glob.glob(EXTENSIONS_PATH+"*.py")
    for fname in files:
        basename = fname[len(EXTENSIONS_PATH):-3]
        modpath = EXTENSIONS_PATH.replace('/', '.')+basename
        module = importlib.import_module(modpath)
        # Finds all python classnames within the file
        mod_members = inspect.getmembers(module, inspect.isclass)
        for (name, path) in mod_members:
            # If the class was not imported, extract the classname
            if str(path) == (modpath + '.' + name):
                classname = name
                # Get the python class object from the classname and module
                handler_class = getattr(module, classname)
                # Extract all URI regular expressions that the handlers manages
                handler = handler_class()
                for regex in handler.resources:
                    # Compiles the regex and maps it to the handler python class
                    tgate_mapper.append((re.compile(regex), handler_class))
                    if not handler.singleonly:
                        tmap_mapper.append((re.compile(regex), handler_class))

except Exception as e:
    raise Exception("Fatal Error loading handlers: %s" % e.message)


def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # Extracting requested values
    req_path = env.get("PATH_INFO", "/")
    req_datetime = env.get("HTTP_ACCEPT_DATETIME")

    # Standard Headers
    headers = [('Content-Type', 'text/html')]

    # Processing request type and path
    req_path = req_path.lstrip('/')
    req_type = req_path.split('/', 1)[0]

    # TimeGate Request
    if req_type == URI_PARTS['G']:
        try:
            return timegate(req_path, start_response, req_datetime)
        except TimegateError as e:
            return resperror(e.status, e.message,
                                  start_response, headers)

    # TimeMap Request
    elif req_type == URI_PARTS['T']:
        try:
            return timemap(req_path, start_response, req_datetime)
        except TimegateError as e:
            return resperror(e.status, e.message,
                                  start_response, headers)

    # Unknown Request
    else:
        status = 404
        message = "Service request type '%s' does not match '%s' or '%s'" % \
                  (req_type, URI_PARTS['T'], URI_PARTS['G'])
        return resperror(status, message, start_response, headers)


def parsedt(datestr):
    """
    Parses the requested date string into a dateutil time object
    Raises DateTimeError if the parse fails to produce a datetime.
    :param datestr: A date string, in a common format.
    :return: the dateutil time object
    """
    try:
        date = dateparser.parse(datestr)
        return date
    except Exception as e:
        raise DateTimeError("Error parsing 'Accept-Datetime: %s' \n"
                               "Message: %s" % (datestr, e.message))


def parseuri(pathstr, methodstr):
    """
    Parses the requested URI string.
    Raises URIRequestError if the parse fails to recognize a valid URI
    :param urlstr: A URI string, in a common format.
    :return: the URI string object
    """

    print pathstr

    try:
        #removes leading 'method/' and replaces whitespaces
        path = pathstr[len(methodstr+'/'):].replace(' ', '%20')

        # Trying to fix incomplete URI
        if not bool(HTTPRE.match(path)):
            if not bool(WWWRE.match(path)):
                path = 'www.'+path
            path = 'http://'+path

        parsed = urlparse(path, scheme='http')
        return parsed.geturl()
    except Exception as e:
        raise URIRequestError("Error: Cannot parse requested path '%s' \n"
                              "message: %s" % (pathstr, e.message))


def resperror(status, message, start_response, headers):
    """
    Returns an error message to the user
    :param status:
    :param message:
    :param start_response:
    :param headers:
    :return:
    """
    body = ["%s \n %s \n" % (status, message)]
    start_response(HTTP_STATUS[status], headers)
    return body


def respmemento(memento, uri_r, start_response, singleonly=False):
    """
    Returns the best Memento requested by the user
    :param memento:
    :param start_response:
    :return:
    """

    #TODO encoding response as utf8

    linkheaderval = '<%s>; rel="original"' % uri_r.encode('utf8')
    if not singleonly:
        linkheaderval += ', <%s/%s/%s>; rel="timemap"' % (HOST, URI_PARTS['T'], uri_r.encode('utf8'))

    status = 302
    headers = [
        ('Date', time.strftime(DATEFMT, time.gmtime())),
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', memento.encode('utf8')),
        ('Link', linkheaderval)
    ]
    # TODO put all normal headers in conf.constants
    body = []
    start_response(HTTP_STATUS[status], headers)
    return body


def resptimemap(mementos, uri_r, start_response):
    """
    Creates and sends a timemap response.
    :param mementos: A list of (uri, datetime) tuples representing a timemap
    :param uri_r: The URI-R of the original resource
    :param start_response: WSGI callback function
    :return: The timemap body as a list of one element
    """

    # Adds Original, TimeGate and TimeMap links
    original_link = '<%s>; rel="original"' % uri_r.encode('utf8')
    timefate_link = '<%s/%s/%s>; rel="timegate"' % (HOST, URI_PARTS['G'], uri_r.encode('utf8'))
    self_link = '<%s/%s/%s>; rel="self"; type="application/link-format"' % (HOST, URI_PARTS['T'], uri_r.encode('utf8'))

    # Browse through Mementos to find the first and the last
    # Generates TimeMap links list in the process
    mementos_links = []
    if mementos:
        first_url = mementos[0][0]
        first_date = dateparser.parse(mementos[0][1])
        last_url = mementos[0][0]
        last_date = dateparser.parse(mementos[0][1])

        for (urlstr, datestr) in mementos:
            date = dateparser.parse(datestr)
            if date < first_date:
                first_date = date
                first_url = urlstr
            elif date > last_date:
                last_date = date
                last_url = urlstr

            linkstr = '<%s>; rel="memento"; datetime="%s"' % (urlstr.encode('utf8'), datestr.encode('utf8'))
            mementos_links.append(linkstr)
        first_datestr = first_date.strftime(DATEFMT).encode('utf8')
        last_datestr = last_date.strftime(DATEFMT).encode('utf8')
        firstlink = '<%s>; rel="first memento"; datetime="%s"' % (first_url.encode('utf8'), first_datestr)
        lastlink = '<%s>; rel="last memento"; datetime="%s"' % (last_url.encode('utf8'), last_datestr)
        mementos_links.insert(0, lastlink)
        mementos_links.insert(0, firstlink)
        self_link = '%s; from="%s"; until="%s"' % (self_link, first_datestr, last_datestr)
    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timefate_link, self_link]
    links.extend(mementos_links)
    body = ',\n'.join(links) + '\n'

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', time.strftime(DATEFMT, time.gmtime())),
        ('Content-Length', str(len(body))),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    return [body]


def loadhandler(uri, singlerequest=False):
    """
    Loads the handler for the requested URI if it exists.
    :param uri: The URI to match to a handler
    :return: the handler object
    Raises URIRequestError if no handler matches this URI
    """

    if singlerequest:
        mapper = tgate_mapper
        method = 'timegate'
    else:
        mapper = tmap_mapper
        method = 'timemap'

    #TODO define what to do if multiple matches
    for (regex, handler) in mapper:
        if bool(regex.match(uri)):
            return handler()

    raise URIRequestError('Cannot find any %s handler for %s' % (method, uri), 404)


def closest(timemap, accept_datetime):
    """
    Finds the chronologically closest memento
    :param timemap:
    :param accept_datetime: the time object
    :return:
    """

    delta = timedelta.max
    memento = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dateparser.parse(dt))
        if diff < delta:
            memento = url
            delta = diff

    return memento


def parse_response(handler_response):
    """
    Controls and parses the response from the Handler. Also extracts URI-R if provided
    as a tuple with the form (URI, None) in the list.
    :param handler_response: Either None, a tuple (URI, date) or a list of (URI, date)
    where one tuple can have 'None' date to indicate that this URI is the original resource's.
    :return: A tuple (URI-R, Mementos) where Mementos is a (URI, date)-list of
    all Mementos. In the response, and all URIs/dates are strings and are valid.
    """

    mementos = []

    # Check if Empty or if tuple
    if not handler_response:
        return (None, None)
    elif isinstance(handler_response, tuple):
        handler_response = [handler_response]
    elif not isinstance(handler_response, list):
        raise Exception('handler_response must be either None, 2-Tuple or 2-Tuple array')

    try:
        for (url, date) in handler_response:
            url_r = None
            valid_urlstr = urlparse(url).geturl()
            if date:
                valid_datestr = dateparser.parse(date).strftime(DATEFMT)
                mementos.append((valid_urlstr, valid_datestr))
            else:
                #(url, None) represents the original resource
                url_r = valid_urlstr

        return (url_r, mementos)

    except Exception as e:
        raise HandlerError('Bad response from Handler:'
                           'response must be either None, (url, date)-Tuple or (url, date)-Tuple array, where '
                           'url, date are with standards formats  %s' % e.message, 503)


def timegate(req_path, start_response, req_datetime):
    """
    Handles timegate high-level logic. Fetch the Memento for the requested URI
    at the requested date time. Returns a HTTP 302 response if it exists.
    :param req_datetime: The Accept-Datetime string
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """

    # Parses the date time and original resoure URI
    accept_datetime = parsedt(req_datetime)
    uri_r = parseuri(req_path, URI_PARTS['G'])
    # Dynamically loads the handler for that resource
    handler = loadhandler(uri_r, True)
    # Runs the handler's API request for the Memento
    req = handler.get(uri_r, accept_datetime)
    # Verifies and validates handler response
    (uri, mementos) = parse_response(req)
    # If the handler returned several Mementos, take the closest
    memento = closest(mementos, accept_datetime)
    # Generates the TimeGate response body and Headers
    return respmemento(memento, uri_r, start_response, handler.singleonly)

def timemap(req_path, start_response, req_datetime=None):
    """
    Handles TimeMap high-level logic. Fetches all Mementos for an Original
    Resource and builds the TimeMap response. Returns a HTTP 200 response if it
    exists with the timemap in the message body.
    :param req_datetime: The Accept-Datetime string, if provided
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """

    # Parses the date time if it was provided. Parses the original resource URI
    if req_datetime:
        accept_datetime = parsedt(req_datetime)
    else:
        accept_datetime = None
    uri_r = parseuri(req_path, URI_PARTS['T'])
    # Dynamically loads the handler for that resource.
    handler = loadhandler(uri_r, False)
    # Runs the handler's API request for all Mementos
    req = handler.get(uri_r, accept_datetime)
    # Verifies and validates handler response
    (uri, mementos) = parse_response(req)
    # Generates the TimeMap response body and Headers
    return resptimemap(mementos, uri_r, start_response)