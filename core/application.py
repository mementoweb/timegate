__author__ = 'Yorick Chollet'

import importlib
import inspect
import glob
import logging
import json

from core.constants import DATE_FORMAT, CACHE_EXP, CACHE_MAX_SIZE, JSON_URI_PART, LINK_URI_PART,  TIMEGATE_URI_PART, TIMEMAP_URI_PART, HTTP_STATUS, EXTENSIONS_PATH, LOG_FORMAT, CACHE_ACTIVATED, STRICT_TIME, HOST, RESOURCE_TYPE, BASE_URI
from errors.timegateerrors import TimegateError, URIRequestError, CacheError
from core.cache import Cache
from core.handler import validate_response, Handler
from core.tgutils import nowstr, validate_req_datetime, validate_req_uri, best, date_str, now
from core.constants import CACHE_FILE, CACHE_RWLOCK, CACHE_DLOCK, CACHE_TOLERANCE



# Initialization code
# Logger configuration
# logging.basicConfig(filename=LOG_FILE, filemode='w',
#                     format=LOG_FMT, level=logging.INFO) # release
logging.basicConfig(filemode='w', format=LOG_FORMAT, level=logging.DEBUG)
logging.getLogger('uwsgi').setLevel(logging.WARNING)

# Handler Loading
found_handlers = 0
api_handler = None
try:
    # Finds the paths of every python modules in the extension folder
    files = [filename[:-3] for filename in glob.glob(EXTENSIONS_PATH+"*.py")]
    for module_path in files:
        # Imports the python module
        module_identifier = module_path.replace('/', '.')
        module = importlib.import_module(module_identifier)
        # Finds all python classes within the module
        mod_members = inspect.getmembers(module, inspect.isclass)
        for (name, handler_class) in mod_members:
            # If the class found is not imported from another path, and is a Handler
            if (str(handler_class) == (module_identifier + '.' + name)
                    and issubclass(handler_class, Handler)):
                api_handler = handler_class()
                found_handlers += 1
                logging.info("Found handler %s" % handler_class)
                if found_handlers > 1:
                    raise Exception("More than one Handler class file in %s." % EXTENSIONS_PATH)
    if found_handlers == 0:
        raise Exception("No handler found in %s . \n    Make sure that the handler is a subclass of `Handler` of module core.handler." % EXTENSIONS_PATH)
except Exception as e:
    logging.critical("Exception during handler loading: %s" % e.message)
    raise e

# Cache loading
cache_use = False
if CACHE_ACTIVATED:
    try:
        cache = Cache(CACHE_FILE, CACHE_TOLERANCE, CACHE_MAX_SIZE, CACHE_EXP, CACHE_RWLOCK, CACHE_DLOCK)
        cache_use = True
        logging.info("Cached started: cache file: %s, cache refresh: %d seconds, max_size: %d Bytes" % (CACHE_FILE, CACHE_TOLERANCE, CACHE_MAX_SIZE))
    except Exception as e:
        logging.error("Exception during cache loading. Cache deactivated. Check permissions")
else:
    logging.info("Cache not used.")
logging.info("Application loaded. Host: %s" % HOST)


def application(env, start_response):
    """
    WSGI application object. This is the start point of the server. Timegate /
    TimeMap requests are parsed here.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """
    # print "cache size at entry:%d" % cache.getsize()

    # Extracting requested values
    req = env.get('PATH_INFO', '/')
    req_datetime = env.get('HTTP_ACCEPT_DATETIME')
    req_met = env.get('REQUEST_METHOD')
    req_mime = env.get('HTTP_ACCEPT')
    logging.info("Incoming request: %s %s, Accept-Datetime: %s, Accept: %s" % (
                 req_met, req, req_datetime, req_mime))


    # Escaping all other than 'GET' requests:
    if req_met != 'GET' and req_met != 'HEAD':
        status = 405
        message = "Request method '%s' not allowed." % req_met
        return error_response(status, start_response, message)

    # Processing request service type and path
    req = req.lstrip('/')
    req_type = req.split('/', 1)[0]

    # Serving TimeGate Request
    if req_type == TIMEGATE_URI_PART:
        try:
            if len(req.split('/', 1)) > 1:
                #removes leading 'TIMEGATESTR/'
                req_path = req.split('/', 1)[1]
                return timegate(req_path, start_response, req_datetime)
            else:
                raise TimegateError("Incomplete timegate request. \n"
                                    "    Syntax: GET /timegate/:resource", 400)
        except TimegateError as e:
            logging.info("End of timegate request due to TimegateError : %s" % e.message)
            return error_response(e.status, start_response, e.message)

    # Serving TimeMap Request
    elif req_type == TIMEMAP_URI_PART:
        try:
            if len(req.split(('/'), 2)) > 2:
                # gets the method (JSON or LINK)
                req_mime = req.split('/', 2)[1]
                #removes leading 'TIMEMAPSTR/MIME_TYPE/'
                req_path = req.split('/', 2)[2]
                return timemap(req_path, req_mime, start_response)
            else:
                raise TimegateError("Incomplete timemap request. \n"
                                    "    Syntax: GET /timemap/:type/:resource", 400)
        except TimegateError as e:
            logging.info("End of timegate request due to TimegateError : %s" % e.message)
            return error_response(e.status, start_response, e.message)

    # Unknown Service Request
    else:
        status = 400
        message = "Service request type '%s' does not match '%s' or '%s'" % (
                  req_type, TIMEMAP_URI_PART, TIMEGATE_URI_PART)
        return error_response(status, start_response, message)


def error_response(status, start_response, message="Internal server error."):
    """
    Returns an error message to the user
    :param status: HTTP Status of the error
    :param message: The error message
    :param start_response: WSGI callback function
    :param headers: Error HTTP headers
    :return: The HTTP body as a list of one element
    """
    body = "%s \n %s \n" % (status, message)

    # Standard response header
    headers = [
        ('Date', nowstr()),  # TODO check timezone
        ('Vary', 'accept-datetime'),
        ('Content-Length',  str(len(body))),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close')
    ]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d Error: %s" % (status, message))
    return [body]


def memento_response(uri_m, uri_r, resource, start_response, batch_requests=True):
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
        timemap_link = '%s/%s/%s/%s' % (HOST, TIMEMAP_URI_PART, LINK_URI_PART, resource)
        timemap_json = '%s/%s/%s/%s' % (HOST, TIMEMAP_URI_PART, JSON_URI_PART, resource)
        linkheaderval += ', <%s>; rel="timemap";' \
                         ' type="application/link-format"' % timemap_link
        linkheaderval += ', <%s>; rel="timemap";' \
                         ' type="application/json"' % timemap_json
    linkheaderval += ', <%s>; rel="memento";' % uri_m

    linkheaderval = linkheaderval

    status = 302
    headers = [
        ('Date', nowstr()),  # TODO check timezone
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


def timemap_link_response(mementos, uri_r, resource, start_response):
    """
    Creates and sends a timemap response.
    :param mementos: A sorted list of (uri_str, datetime_obj) tuples representing a timemap
    :param uri_r: The URI-R of the original resource
    :param start_response: WSGI callback function
    :return: The HTTP body as a list of one element
    """
    assert len(mementos) >= 1

    # Adds Original, TimeGate and TimeMap links
    original_link = '<%s>; rel="original"' % uri_r
    timegate_link = '<%s/%s/%s>; rel="timegate"' % (
        HOST, TIMEGATE_URI_PART, resource)
    link_self = '<%s/%s/%s/%s>; rel="self"; type="application/link-format"' % (
        HOST, TIMEMAP_URI_PART, LINK_URI_PART, resource)
    json_self = '<%s/%s/%s/%s>; rel="self"; type="application/json"' % (
        HOST, TIMEMAP_URI_PART, JSON_URI_PART, resource)

    # Browse through Mementos to generate the TimeMap links list
    mementos_links = ['<%s>; rel="memento"; datetime="%s"' % (uri, date_str(date))
                      for (uri, date) in mementos]

    # Sets up first and last relations
    if len(mementos_links) == 1:
        mementos_links[0] = mementos_links[0].replace('rel="memento"', 'rel="first last memento"')
    else:
        mementos_links[0] = mementos_links[0].replace('rel="memento"', 'rel="first memento"')
        mementos_links[-1] = mementos_links[-1].replace('rel="memento"', 'rel="last memento"')

    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timegate_link, link_self, json_self]
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


def timemap_json_response(mementos, uri_r, resource, start_response):
    """
    Creates and sends a timemap response.
    :param mementos: A sorted list of (uri_str, datetime_obj) tuples representing a timemap
    :param uri_r: The URI-R of the original resource
    :param start_response: WSGI callback function
    :return: The HTTP body as a list of one element
    """
    assert len(mementos) >= 1

    # JSON response
    ret = {}

    ret['original_uri'] = uri_r
    ret['timegate_uri'] = '%s/%s/%s' % (HOST, TIMEGATE_URI_PART, resource)

    # Browse through Mementos to generate TimeMap links JSON objects
    mementos_links = [{'uri': urlstr, 'datetime': date_str(date)}
                      for (urlstr, date) in mementos]

    # Sets up first and last
    first_datestr = mementos[0][1].strftime(DATE_FORMAT)
    firstlink = {'uri': mementos[0][0],
                 'datetime': first_datestr}
    last_datestr = mementos[-1][1].strftime(DATE_FORMAT)
    lastlink = {'uri': mementos[-1][0],
                'datetime': last_datestr}

    ret['mementos'] = {'last': lastlink,
                       'first': firstlink,
                       'list': mementos_links}

    ret['timemap_uri'] = {
        'json_format': '%s/%s/%s/%s' % (HOST, TIMEMAP_URI_PART, JSON_URI_PART, resource),
        'link_format': '%s/%s/%s/%s' % (HOST, TIMEMAP_URI_PART, LINK_URI_PART, resource)
    }

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
    Loads the handler for the requested URI if it exists.
    :param uri: The URI to match to a handler
    :return: the handler object
    """
    if not uri.startswith(BASE_URI):
        uri = BASE_URI + uri
    return (api_handler, uri)


def get_and_cache(uri_r, getter, *args, **kwargs):
    if cache_use:
        return cache.refresh(uri_r, getter, *args, **kwargs)
    else:
        return validate_response(getter(*args, **kwargs))


def get_if_cached(uri_r, accept_datetime=None):
    if cache_use:
        try:
            if accept_datetime:
                return cache.get_until(uri_r, accept_datetime)
            else:
                return cache.get_all(uri_r)
        except CacheError as ce:
            # cache_use = False TODO fix
            pass
    return None


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

    resource = validate_req_uri(req_path)
    # Dynamically loads the handler for that resource
    (handler, uri_r) = loadhandler(resource)
    # Runs the handler's API request for the Memento
    if hasattr(handler, 'get_all_mementos'):  # TODO put in const
        mementos = get_if_cached(uri_r, accept_datetime)
        if mementos is None:
            if hasattr(handler, 'get_memento'):
                logging.debug('Using single-request mode.')
                mementos = validate_response(handler.get_memento(uri_r, accept_datetime))
            else:
                logging.debug('Using multiple-request mode.')
                mementos = get_and_cache(uri_r, handler.get_all_mementos, uri_r)
    elif hasattr(handler, 'get_memento'):
        mementos = validate_response(handler.get_memento(uri_r, accept_datetime))
    else:
        logging.error("NotImplementedError: Handler has neither get_memento nor get_all_mementos function.")
        raise TimegateError("NotImplementedError: Handler has neither get_memento nor get_all_mementos function.", 502)  # TODO put in const

    # If the handler returned several Mementos, take the closest
    memento = best(mementos, accept_datetime, RESOURCE_TYPE)
    return memento_response(memento, uri_r, resource, start_response, hasattr(handler, 'get_all_mementos'))


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
    if not (req_mime == JSON_URI_PART or req_mime == LINK_URI_PART):
        raise URIRequestError('Mime type (%s) empty or unknown. Request must be GET timemap/%s/... or GET timemap/%s/... '
                              % (req_mime, JSON_URI_PART, LINK_URI_PART), 400)

    resource = validate_req_uri(req_path)
    # Dynamically loads the handler for that resource.
    (handler, uri_r) = loadhandler(resource)

    if hasattr(handler, 'get_all_mementos'):
        mementos = get_if_cached(uri_r)
        if mementos is None:
            mementos = get_and_cache(uri_r, handler.get_all_mementos, uri_r)
    else:
        raise TimegateError("Handler cannot serve timemaps.", 400)  # TODO put in const

    # Generates the TimeMap response body and Headers
    if req_mime.startswith(JSON_URI_PART):
        return timemap_json_response(mementos, uri_r, resource, start_response)
    else:
        return timemap_link_response(mementos, uri_r, resource, start_response)
