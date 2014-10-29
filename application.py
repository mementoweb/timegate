__author__ = 'Yorick Chollet'

import importlib
import inspect
import glob
import logging
import json

import re

from conf.constants import DATEFMT, JSONSTR, LINKSTR,  TIMEGATESTR, TIMEMAPSTR, HTTP_STATUS, EXTENSIONS_PATH, LOG_FMT, MIME_JSON
from conf.config import CACHE_USE, STRICT_TIME, HOST, SINGLE_HANDLER
from errors.urierror import URIRequestError
from errors.timegateerror import TimegateError
from core.cache import Cache
from core.handler import validate_response
from tgutils import nowstr, validate_req_datetime, validate_req_uri, closest, closest_past, date_str, now


# Initialization code
# Logger configuration
# logging.basicConfig(filename=LOG_FILE, filemode='w',
#                     format=LOG_FMT, level=logging.INFO) # release
logging.basicConfig(filemode='w', format=LOG_FMT, level=logging.DEBUG)  # DEBUG
# logging.getLogger('uwsgi').setLevel(logging.WARNING)

# Builds the mapper from URI regular expression to handler class
'''
try:
    handlers_ct = 0
    tgate_mapper = []  # TODO merge those
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
                    if handler.single_requests:
                        tgate_mapper.append((re.compile(regex), handler_class))
                    if handler.batch_requests:
                        tmap_mapper.append((re.compile(regex), handler_class))
    logging.info("Loaded %d handlers for %d regular expressions URI." % (
                 handlers_ct, len(tgate_mapper)))
     '''

handlers_ct = 0
api_handler = None
mapper = []

try:
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
                api_handler = handler_class()
                logging.info("Found handler %s" % classname)
                handlers_ct += 1
                if SINGLE_HANDLER and handlers_ct > 1:
                    raise Exception("More than one python class file"
                                    " in handler directory found. ")
                else:
                    for regex in api_handler.resources:
                        # Compiles the regex and maps it to the handler python class
                        mapper.append((re.compile(regex), api_handler))
    logging.info("Loaded %d handlers for %d regular expressions URI." % (
                handlers_ct, len(mapper)))

except Exception as e:
    logging.debug("Exception during handler loading: %s" % e.message)
    raise Exception("Fatal Error loading handlers: %s" % e.message)

# Cache loading
try:
    cache = Cache(enabled=CACHE_USE)
except Exception as e:
    logging.debug("Exception during cache loading.")
    raise Exception("Fatal Error loading cache: %s" % e.message)


logging.info("Application loaded. Host: %s" % HOST)

def application(env, start_response):
    """
    WSGI application object. This is the start point of the server. Timegate /
    TimeMap requests are parsed here.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # Extracting requested values
    req = env.get('PATH_INFO', '/')
    req_datetime = env.get('HTTP_ACCEPT_DATETIME')
    req_met = env.get('REQUEST_METHOD')
    req_mime = env.get('HTTP_ACCEPT')
    logging.info("Incoming request: %s %s, Accept-Datetime: %s, Accept: %s" % (
                 req_met, req, req_datetime, req_mime))

    # Standard response header
    headers = [('Content-Type', 'text/html')]

    # Escaping all other than 'GET' requests:
    if req_met != 'GET' and req_met != 'HEAD':
        status = 405
        message = "Request method '%s' not allowed." % req_met
        return resperror(status, message, start_response, headers)

    # Processing request service type and path
    req = req.lstrip('/')
    req_type = req.split('/', 1)[0]

    # Serving TimeGate Request
    if req_type == TIMEGATESTR:
        try:
            #removes leading 'TIMEGATESTR/'
            req_path = req.split('/', 1)[1]
            return timegate(req_path, start_response, req_datetime)
        except TimegateError as e:
            return resperror(e.status, e.message,
                             start_response, headers)

    # Serving TimeMap Request
    elif req_type == TIMEMAPSTR:
        try:
            # gets the method (JSON or LINK)
            req_mime = req.split('/', 2)[1]
            #removes leading 'TIMEMAPSTR/MIME_TYPE/'
            req_path = req.split('/', 2)[2]
            return timemap(req_path, req_mime, start_response)
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
    :param status: HTTP Status of the error
    :param message: The error message
    :param start_response: WSGI callback function
    :param headers: Error HTTP headers
    :return: The HTTP body as a list of one element
    """
    body = ["%s \n %s \n" % (status, message)]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d Error: %s" % (status, message))
    return body


def respmemento(uri_m, uri_r, start_response, batch_requests=True):
    """
    Returns a 302 redirection to the best Memento
    for a resource and a datetime requested by the user.
    :param uri_m: The URI string of the best memento.
    :param start_response: WSGI callback function
    :return: The HTTP body as a list of one element
    """

    #TODO encoding response as utf8 ?!?

    linkheaderval = '<%s>; rel="original"' % uri_r
    if batch_requests:
        timemap_link = '%s/%s/%s/%s' % (HOST, TIMEMAPSTR, LINKSTR, uri_r)
        timemap_json = '%s/%s/%s/%s' % (HOST, TIMEMAPSTR, JSONSTR, uri_r)
        linkheaderval += ', <%s>; rel="timemap";' \
                         ' type="application/link-format"' % timemap_link
        linkheaderval += ', <%s>; rel="timemap";' \
                         ' type="application/json"' % timemap_json

    linkheaderval = linkheaderval

    status = 302
    headers = [
        ('Date', nowstr()), # TODO check timezone
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', uri_m),
        ('Link', linkheaderval)
    ]
    # TODO put all normal headers in conf.constants
    body = []
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, Memento=%s for URI-R=%s" %
                 (status, uri_m, uri_r))
    return body


def create_tm_link(mementos, uri_r, start_response):
    """
    Creates and sends a timemap response.
    :param mementos: A list of (uri_str, datetime_obj) tuples representing a timemap
    :param uri_r: The URI-R of the original resource
    :param start_response: WSGI callback function
    :return: The HTTP body as a list of one element
    """

    # Adds Original, TimeGate and TimeMap links
    original_link = '<%s>; rel="original"' % uri_r
    timegate_link = '<%s/%s/%s>; rel="timegate"' % (
        HOST, TIMEGATESTR, uri_r)
    self_link = '<%s/%s/%s/%s>; rel="self"; type="application/link-format"' % (
        HOST, TIMEMAPSTR, LINKSTR, uri_r)
    other_link = '<%s/%s/%s/%s>; rel="self"; type="application/json"' % (
        HOST, TIMEMAPSTR, JSONSTR, uri_r)

    # Browse through Mementos to find the first and the last
    # Generates TimeMap links list in the process
    mementos_links = []
    if mementos:
        first_url = mementos[0][0]
        first_date = mementos[0][1]
        last_url = mementos[0][0]
        last_date = mementos[0][1]

        for (urlstr, date) in mementos:
            if date < first_date:
                first_date = date
                first_url = urlstr
            elif date > last_date:
                last_date = date
                last_url = urlstr
            linkstr = '<%s>; rel="memento"; datetime="%s"' % (
                urlstr, date_str(date))
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
        other_link = '%s; from="%s"; until="%s"' % (
            other_link, first_datestr, last_datestr)

    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timegate_link, self_link, other_link]
    links.extend(mementos_links)  # TODO modularizer ca...
    body = ',\n'.join(links) + '\n'

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', nowstr()),  # TODO check timezone
        ('Content-Length', str(len(body))),
        ('Content-Type', 'application/link-format'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, LINK TimeMap of size %d for URI-R=%s" %
                 (status, len(mementos), uri_r))
    return [body]

def create_tm_json(mementos, uri_r, start_response):
    """
    Creates and sends a timemap response.
    :param mementos: A list of (uri_str, datetime_obj) tuples representing a timemap
    :param uri_r: The URI-R of the original resource
    :param start_response: WSGI callback function
    :return: The HTTP body as a list of one element
    """
    # TODO clean and docstring
    ret = {}

    ret['original_uri'] = uri_r
    ret['timegate_uri'] = '%s/%s/%s' % (HOST, TIMEGATESTR, uri_r)
    ret['timemap_uri'] = {
        'json_format': '%s/%s/%s/%s' % (HOST, TIMEMAPSTR, JSONSTR, uri_r),
        'link_format': '%s/%s/%s/%s' % (HOST, TIMEMAPSTR, LINKSTR, uri_r)
    }

    # Browse through Mementos to find the first and the last
    # Generates TimeMap links list in the process
    mementos_links = []
    if mementos:
        first_url = mementos[0][0]
        first_date = mementos[0][1]
        last_url = mementos[0][0]
        last_date = mementos[0][1]

        for (urlstr, date) in mementos:
            if date < first_date:
                first_date = date
                first_url = urlstr
            elif date > last_date:
                last_date = date
                last_url = urlstr
            linkstr = {'memento': urlstr,
                       'datetime': date_str(date)}
            mementos_links.append(linkstr)

        first_datestr = first_date.strftime(DATEFMT)
        last_datestr = last_date.strftime(DATEFMT)
        firstlink = {'memento': first_url,
                     'datetime': first_datestr}
        lastlink = {'memento': last_url,
                    'datetime': last_datestr}
        ret['from'] = first_datestr
        ret['until'] = last_datestr
        ret['mementos'] = {'last': firstlink,
                           'first': lastlink,
                           'all': mementos_links}

    body = json.dumps(ret)

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', nowstr()),  # TODO check timezone
        ('Content-Length', str(len(body))),
        ('Content-Type', 'application/json'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, JSON TimeMap of size %d for URI-R=%s" %
                 (status, len(mementos), uri_r))
    return [body]


def loadhandler(uri):
    """
    Loads the first handler for the requested URI if it exists.
    :param uri: The URI to match to a handler
    :param singlerequest: Boolean indicating if the requests is for a single
    memento (true) or for a timemap (false). If False (default), then the handler MUST allow
    batch requests.
    :return: the handler object
    Raises URIRequestError if no handler matches this URI
    """

    if SINGLE_HANDLER:
        return api_handler
    else:
        #Finds the first handler which regex match with the requested URI-R
        for (regex, handler) in mapper:
            if bool(regex.match(uri)):
                logging.debug("%s matched pattern %s of handler %s" % (uri, regex.pattern, handler))
                return handler

    raise URIRequestError('Cannot find any handler for %s' % uri, 404)




def timegate(req_path, start_response, req_datetime):
    """
    Handles timegate high-level logic. Fetch the Memento for the requested URI
    at the requested date time. Returns a HTTP 302 response if it exists.
    If the resource handler allows batch requests, then the result may be
    cached.
    :param req_datetime: The Accept-Datetime string
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """

    # Parses the date time and original resoure URI
    if req_datetime is None or req_datetime == '':
        accept_datetime = now()
    else:
        accept_datetime = validate_req_datetime(req_datetime, STRICT_TIME)
    uri_r = validate_req_uri(req_path)
    # Dynamically loads the handler for that resource
    handler = loadhandler(uri_r)

    # Runs the handler's API request for the Memento
    if hasattr(handler, 'getall'):  # TODO put in const
        mementos = cache.get_until(uri_r, accept_datetime)
        if mementos is None:
            if hasattr(handler, 'getone'):
                mementos = validate_response(handler.getone(uri_r, accept_datetime))
            else:
                mementos = cache.refresh(uri_r, handler.getall, uri_r)
    elif hasattr(handler, 'getone'):
        mementos = validate_response(handler.getone(uri_r, accept_datetime))
    else:
        raise TimegateError("NotImplementedError: Handler has neither getone nor getall function.", 503)  # TODO put in const
    assert mementos

    # If the handler returned several Mementos, take the closest
    memento = closest_past(mementos, accept_datetime)
    # Generates the TimeGate response body and Headers
    return respmemento(memento, uri_r, start_response, hasattr(handler, 'getall'))


def timemap(req_path, req_mime, start_response):
    """
    Handles TimeMap high-level logic. Fetches all Mementos for an Original
    Resource and builds the TimeMap response. Returns a HTTP 200 response if it
    exists with the timemap in the message body.
    :param req_datetime: The Accept-Datetime string, if provided
    :param req_path: The requested original resource URI
    :param start_response: WSGI callback function
    :return: The body of the HTTP response
    """
    if not (req_mime == JSONSTR or req_mime == LINKSTR):
        raise URIRequestError('Mime type (%s) unknown. must be %s or %s'
                              % (req_mime, JSONSTR, LINKSTR), 400)

    uri_r = validate_req_uri(req_path)
    # Dynamically loads the handler for that resource.
    handler = loadhandler(uri_r)

    if hasattr(handler, 'getall'):
        mementos = cache.get_all(uri_r)
        if mementos is None:
            mementos = cache.refresh(uri_r, handler.getall, uri_r)
    else:
        raise TimegateError("NotImplementedError: Handler has neither getone nor getall function.", 503)  # TODO put in const
    assert mementos

    # Generates the TimeMap response body and Headers
    if req_mime.startswith(JSONSTR):
        return create_tm_json(mementos, uri_r, start_response)
    else:  # TODO define default (crash / link)
        return create_tm_link(mementos, uri_r, start_response)