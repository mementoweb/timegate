__author__ = 'Yorick Chollet'

import importlib
import inspect
from time import strftime, gmtime
import datetime
import re
import glob
from urlparse import urlparse
import logging

from dateutil.parser import parse as parse_datestr
from dateutil.tz import tzutc

from conf.constants import HTTPRE, WWWRE, DATEFMT, USE_CACHE, TIMEGATESTR, TIMEMAPSTR, HTTP_STATUS, HOST, EXTENSIONS_PATH, LOG_FMT, LOG_FILE, STRICT_TIME, BEST
from errors.urierror import URIRequestError
from errors.dateerror import DateTimeError
from errors.timegateerror import TimegateError
from errors.handlererror import HandlerError
from core.cache import Cache

# Initialization code
# Logger configuration
# logging.basicConfig(filename=LOG_FILE, filemode='w',
#                     format=LOG_FMT, level=logging.INFO) # release
logging.basicConfig(filemode='w', format=LOG_FMT, level=logging.DEBUG) # DEBUG

# TODO define request url, define if JSON/XML allowed?

# Builds the mapper from URI regular expression to handler class
try:
    handlers_ct = 0
    tgate_mapper = [] #TODO merge those
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
                handlers_ct += 1
                for regex in handler.resources:
                    # Compiles the regex and maps it to the handler python class
                    tgate_mapper.append((re.compile(regex), handler_class))
                    if not handler.singleonly:
                        tmap_mapper.append((re.compile(regex), handler_class))
    logging.info("Loaded %d handlers for %d regular expressions URI." % (
                 handlers_ct, len(tgate_mapper)))
except Exception as e:
    logging.debug("Exception during handler loading.")
    raise Exception("Fatal Error loading handlers: %s" % e.message)



def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # Extracting requested values
    req_path = env.get('PATH_INFO', '/')
    req_datetime = env.get('HTTP_ACCEPT_DATETIME')
    req_meth = env.get('REQUEST_METHOD')
    logging.info("Incoming request: %s %s Accept-Datetime: %s" % (
                 req_meth, req_path, req_datetime))

    # Standard response header
    headers = [('Content-Type', 'text/html')]

    # Escaping all other than 'GET' requests:
    if req_meth != 'GET' and req_meth != 'HEAD':
        status = 405
        message = "Request method '%s' not allowed." % req_meth
        return resperror(status, message, start_response, headers)

    # Processing request service type and path
    req_path = req_path.lstrip('/')
    req_type = req_path.split('/', 1)[0]

    # Serving TimeGate Request
    if req_type == TIMEGATESTR:
        try:
            return timegate(req_path, start_response, req_datetime)
        except TimegateError as e:
            return resperror(e.status, e.message,
                             start_response, headers)

    # Serving TimeMap Request
    elif req_type == TIMEMAPSTR:
        try:
            return timemap(req_path, start_response)
        except TimegateError as e:
            return resperror(e.status, e.message,
                             start_response, headers)

    # Unknown Service Request
    else:
        status = 400
        message = "Service request type '%s' does not match '%s' or '%s'" % (
                  req_type, URI_PARTS['T'], URI_PARTS['G'])
        return resperror(status, message, start_response, headers)


def validate_datetime(datestr, strict=True):
    """
    Parses the requested date string into a dateutil time object
    Raises DateTimeError if the parse fails to produce a datetime.
    :param datestr: A date string, in a common format.
    :return: the dateutil time object
    """
    try:
        if strict:
            date = datetime.strptime(datestr, DATEFMT)
        else:
            date = parse_datestr(datestr, fuzzy=True).replace(tzinfo=tzutc())
        logging.debug("Accept datetime parsed to: "+date.strftime(DATEFMT))
        return date
    except Exception as e:
        raise DateTimeError("Error parsing 'Accept-Datetime: %s' \n"
                            "Message: %s" % (datestr, e.message))


def validate_uri(pathstr, methodstr):
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


def validate_response(handler_response):
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
        url_r = None
        for (url, date) in handler_response:
            valid_urlstr = str(urlparse(url).geturl())
            if date:
                valid_datestr = str(parse_datestr(date).strftime(DATEFMT))
                mementos.append((valid_urlstr, valid_datestr))
            else:
                #(url, None) represents the original resource
                url_r = valid_urlstr

        return (url_r, mementos)

    except Exception as e:
        raise HandlerError('Bad response from Handler:'
                           'response must be either None, (url, date)-Tuple or'
                           ' (url, date)-Tuple array, where '
                           'url, date are with standards formats  %s'
                           % e.message, 503)


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
    logging.info("Returning %d Error: %s" % (status, message))
    return body


def respmemento(memento, uri_r, start_response, singleonly=False):
    """
    Returns the best Memento requested by the user
    :param memento:
    :param start_response:
    :return:
    """

    #TODO encoding response as utf8 ?!?

    linkheaderval = '<%s>; rel="original"' % uri_r
    if not singleonly:
        timemaplink = '%s/%s/%s' % (HOST, TIMEMAPSTR, uri_r)
        linkheaderval += ', <%s>; rel="timemap"' % timemaplink

    linkheaderval = linkheaderval

    status = 302
    headers = [
        ('Date', strftime(DATEFMT, gmtime()).encode('utf8')),
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', memento),
        ('Link', linkheaderval)
    ]
    # TODO put all normal headers in conf.constants
    body = []
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, Memento=%s for URI-R=%s" %
                 (status, memento, uri_r))
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
    original_link = '<%s>; rel="original"' % uri_r
    timegate_link = '<%s/%s/%s>; rel="timegate"' % (
        HOST, TIMEGATESTR, uri_r)
    self_link = '<%s/%s/%s>; rel="self"; type="application/link-format"' % (
        HOST, TIMEMAPSTR, uri_r)

    # Browse through Mementos to find the first and the last
    # Generates TimeMap links list in the process
    mementos_links = []
    if mementos:
        first_url = mementos[0][0]
        first_date = parse_datestr(mementos[0][1])
        last_url = mementos[0][0]
        last_date = parse_datestr(mementos[0][1])

        for (urlstr, datestr) in mementos:
            date = parse_datestr(datestr)
            if date < first_date:
                first_date = date
                first_url = urlstr
            elif date > last_date:
                last_date = date
                last_url = urlstr

            linkstr = '<%s>; rel="memento"; datetime="%s"' % (
                urlstr, datestr)
            mementos_links.append(linkstr)
        first_datestr = first_date.strftime(DATEFMT)
        last_datestr = last_date.strftime(DATEFMT)
        firstlink = '<%s>; rel="first memento"; datetime="%s"' % (
            first_url, first_datestr)
        lastlink = '<%s>; rel="last memento"; datetime="%s"' % (
            last_url, last_datestr)
        mementos_links.insert(0, lastlink)
        mementos_links.insert(0, firstlink)
        self_link = '%s; from="%s"; until="%s"' % (
            self_link, first_datestr, last_datestr)
    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timegate_link, self_link]
    links.extend(mementos_links) # TODO modularizer ca...
    body = ',\n'.join(links) + '\n'

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', strftime(DATEFMT, gmtime()).encode('utf8')),
        ('Content-Length', str(len(body))),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, TimeMap of size %d for URI-R=%s" %
                 (status, len(mementos), uri_r))
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
            logging.debug("%s matched pattern %s of handler %s" %
                          (uri, regex.pattern, handler))
            return handler()

    raise URIRequestError('Cannot find any %s handler for %s' %
                          (method, uri), 404)


def closest(timemap, accept_datetime):
    """
    Finds the chronologically closest memento
    :param timemap:
    :param accept_datetime: the time object
    :return:
    """

    delta = datetime.timedelta.max
    memento = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - parse_datestr(dt))
        if diff < delta:
            memento = url
            delta = diff

    return memento


def timegate(req_path, start_response, req_datetime):
    """
    Handles timegate high-level logic. Fetch the Memento for the requested URI
    at the requested date time. Returns a HTTP 302 response if it exists.
    :param req_datetime: The Accept-Datetime string
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """

    #TODO define how TimeMap/TimeGate Single/all

    # Parses the date time and original resoure URI
    accept_datetime = validate_datetime(req_datetime, STRICT_TIME)
    uri_r = validate_uri(req_path, TIMEGATESTR)
    # Dynamically loads the handler for that resource
    handler = loadhandler(uri_r, True)
    # Runs the handler's API request for the Memento
    if handler.singleonly: #TODO comment this
        req = handler.getone(uri_r, accept_datetime)
    else:
        req = handler.getall(uri_r)
    # Verifies and validates handler response
    (uri, mementos) = validate_response(req)
    # If the handler returned several Mementos, take the closest
    memento = locals[BEST](mementos, accept_datetime)
    # Generates the TimeGate response body and Headers
    return respmemento(memento, uri_r, start_response, handler.singleonly)

def timemap(req_path, start_response):
    """
    Handles TimeMap high-level logic. Fetches all Mementos for an Original
    Resource and builds the TimeMap response. Returns a HTTP 200 response if it
    exists with the timemap in the message body.
    :param req_datetime: The Accept-Datetime string, if provided
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """
    uri_r = validate_uri(req_path, TIMEMAPSTR)
    # Dynamically loads the handler for that resource.
    handler = loadhandler(uri_r, False)
    # Runs the handler's API request for all Mementos
    req = handler.getall(uri_r)
    # Verifies and validates handler response
    (uri, mementos) = validate_response(req)
    # Generates the TimeMap response body and Headers
    return resptimemap(mementos, uri_r, start_response)