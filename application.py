__author__ = 'Yorick Chollet'

import importlib
import inspect
import glob
import logging

import re

from tgutils import nowstr, parse_date, validate_req_datetime, validate_req_uri, closest
from conf.constants import DATEFMT, USE_CACHE, TIMEGATESTR, TIMEMAPSTR, HTTP_STATUS, HOST, EXTENSIONS_PATH, LOG_FMT, \
    STRICT_TIME
from errors.urierror import URIRequestError
from errors.timegateerror import TimegateError
from core.cache import Cache


# Initialization code
# Logger configuration
# logging.basicConfig(filename=LOG_FILE, filemode='w',
#                     format=LOG_FMT, level=logging.INFO) # release
logging.basicConfig(filemode='w', format=LOG_FMT, level=logging.DEBUG) # DEBUG
logging.getLogger('uwsgi').setLevel(logging.WARNING)

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


try:
    cache = Cache(tolerance=3600, enabled=USE_CACHE) # TODO const
except Exception as e:
    raise Exception("Fatal Error loading cache: %s" % e.message)


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
                  req_type, TIMEMAPSTR, TIMEGATESTR)
        return resperror(status, message, start_response, headers)

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
        ('Date', nowstr()), # TODO check timezone
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
        first_date = parse_date(mementos[0][1])
        last_url = mementos[0][0]
        last_date = parse_date(mementos[0][1])

        for (urlstr, datestr) in mementos:
            date = parse_date(datestr)
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
        ('Date', nowstr()), # TODO check timezone
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
    accept_datetime = validate_req_datetime(req_datetime, STRICT_TIME)
    uri_r = validate_req_uri(req_path, TIMEGATESTR)
    # Dynamically loads the handler for that resource
    handler = loadhandler(uri_r, True)
    # Runs the handler's API request for the Memento
    if handler.singleonly: #TODO comment this
         # Timemaps do not exist for that handler
        mementos = handler.getone(uri_r, accept_datetime)
    else:
        # Query the cache for a timemap old enough
        mementos = cache.get_until(uri_r, accept_datetime, handler.getall, uri_r)
    # If the handler returned several Mementos, take the closest
    memento = closest(mementos, accept_datetime)
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
    uri_r = validate_req_uri(req_path, TIMEMAPSTR)
    # Dynamically loads the handler for that resource.
    handler = loadhandler(uri_r, False)
    # Query the cache for a timemap not older than cache tolerance.
    mementos = cache.get_all(uri_r, handler.getall, uri_r)
    # Generates the TimeMap response body and Headers
    return resptimemap(mementos, uri_r, start_response)