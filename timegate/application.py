# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015, 2016 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Implementation of the TimeGate server."""

from __future__ import absolute_import, print_function

import glob
import importlib
import inspect
import json
import logging

from .cache import Cache
from .constants import (BASE_URI, CACHE_EXP, CACHE_FILE, CACHE_MAX_VALUES,
                        CACHE_TOLERANCE, CACHE_USE, DATE_FORMAT,
                        EXTENSIONS_PATH, HANDLER_MODULE, HOST, HTTP_STATUS,
                        JSON_URI_PART, LINK_URI_PART, LOG_FORMAT,
                        RESOURCE_TYPE, STRICT_TIME, TIMEGATE_URI_PART,
                        TIMEMAP_URI_PART, USE_TIMEMAPS)
from .errors import TimegateError, URIRequestError
from .handler import Handler, parsed_request
from .utils import (best, date_str, get_complete_uri, now, nowstr,
                    parse_req_resource, validate_req_datetime)

PROTO_HOST = "http://" + HOST


def discover_handler(path):
    """Discovers and loads python class in *path* that is a subclass of
    core.handler.Handler.

    :param path: The directory to search in :return: A handler object
    :raises Exception: When no such class is found, or when more than
    one is found

    """
    # Handler Loading
    found_handlers = 0
    api_handler = None
    # Finds the paths of every python modules in the handler folder
    files = [filename[:-3] for filename in glob.glob(path + "*.py")]
    for module_path in files:
        # Imports the python module
        module_identifier = module_path.replace('/', '.')
        module = importlib.import_module(module_identifier)
        # Finds all python classes within the module
        mod_members = inspect.getmembers(module, inspect.isclass)
        for (name, handler_class) in mod_members:
            # If the class found is not imported from another path, and is a
            # Handler
            if str(handler_class) == (module_identifier + '.' + name) and \
                    issubclass(handler_class, Handler):
                api_handler = handler_class()
                found_handlers += 1
                logging.info("Found handler %s" % handler_class)
                if found_handlers > 1:
                    raise Exception(
                        "More than one Handler class file in %s." % path)
    if found_handlers == 0:
        raise Exception(
            "No handler found in %s.\n"
            "Make sure that the handler is a subclass of `Handler` of "
            "module core.handler." % path)
    else:
        return api_handler

# Handler loading
try:
    if HANDLER_MODULE:
        dot_index = HANDLER_MODULE.rfind('.')
        mod = importlib.import_module(HANDLER_MODULE[:dot_index])
        handler_class = getattr(mod, HANDLER_MODULE[dot_index + 1:])
        logging.info("Found handler %s" % handler_class)
        handler = handler_class()
    else:
        handler = discover_handler(EXTENSIONS_PATH)

    HAS_TIMEGATE = hasattr(handler, 'get_memento')
    HAS_TIMEMAP = hasattr(handler, 'get_all_mementos')
    if USE_TIMEMAPS and (not HAS_TIMEMAP):
        logging.error(
            "Handler has no get_all_mementos() function "
            "but is suppose to serve timemaps.")

    if not (HAS_TIMEGATE or HAS_TIMEMAP):
        logging.critical(
            "NotImplementedError: Handler has neither `get_memento` "
            "nor `get_all_mementos` method.")
        raise NotImplementedError(
            "NotImplementedError: Handler has neither `get_memento` "
            "nor `get_all_mementos` method.")

except Exception as e:
    logging.critical("Exception during handler loading: %s" % e)
    raise e

# Cache loading
cache_activated = False
if CACHE_USE:
    try:
        cache = Cache(CACHE_FILE, CACHE_TOLERANCE, CACHE_EXP, CACHE_MAX_VALUES)
        cache_activated = True
        logging.info(
            "Cached started: cache directory: '%s', cache refresh: %d seconds,"
            " max_values: %d TimeMaps" %
            (CACHE_FILE, CACHE_TOLERANCE, CACHE_MAX_VALUES))
    except Exception as e:
        logging.error("Exception during cache loading: %s. Cache deactivated."
                      "Check permissions" % e)
else:
    logging.info("Cache not used.")

logging.info("Application loaded. Host: %s" % HOST)


def application(env, start_response):
    """WSGI application object.

    This is the start point of the TimeGate server.

    TimeMap requests are parsed here.

    :param env: Dictionary containing environment variables from
    the client request.
    :param start_response: Callback function used to send HTTP status
    and headers to the server.
    :return: The response body, in a list of one str element.
    """
    # Extracting HTTP request values

    req_path = env.get('REQUEST_URI', '/')

    # Finds the request type
    tg_index = req_path.find(TIMEGATE_URI_PART + '/')
    tm_index = req_path.find(TIMEMAP_URI_PART + '/')
    # If both are present, take the first one
    if tg_index >= 0 and tm_index >= 0:
        if tg_index > tm_index:
            tg_index = -1
        else:
            tm_index = -1

    req_datetime = env.get('HTTP_ACCEPT_DATETIME')
    req_method = env.get('REQUEST_METHOD')
    req_protocol = env.get("HTTP_X_FORWORDED_PROTO", "http")

    PROTO_HOST = req_protocol + "://" + HOST

    force_cache_refresh = (env.get('HTTP_CACHE CONTROL') == 'no-cache' or
                           env.get('HTTP_CACHE_CONTROL') == 'no-cache')
    logging.info(
        "Incoming request: %s %s, Accept-Datetime: %s , Force Refresh: %s" %
        (req_method, req_path, req_datetime, force_cache_refresh))

    # Escaping all other than 'GET' requests:
    if req_method != 'GET' and req_method != 'HEAD':
        status = 405
        message = "Request method '%s' not allowed." % req_method
        return error_response(status, start_response, message)

    # Serving TimeGate Request
    if tg_index >= 0:
        # Trunkating all before 'timegate/'
        req_path = req_path[tg_index:]
        try:
            if len(req_path.split('/', 1)) > 1:
                # removes leading 'TIMEGATE_URI_PART/'
                req_uri = req_path.split('/', 1)[1]
                return timegate(
                    req_uri,
                    req_datetime,
                    start_response,
                    force_cache_refresh)
            else:
                raise TimegateError("Incomplete timegate request. \n"
                                    "    Syntax: GET /timegate/:resource", 400)
        except TimegateError as e:
            logging.info(
                "End of timegate request due to TimegateError : %s" % e)
            return error_response(e.status, start_response, e)
        except Exception as e:
            logging.critical(
                "End of timegate request due to an unhandled Exception : %s" %
                e)
            return error_response(503, start_response)

    # Serving TimeMap Request
    elif tm_index >= 0:
        # Trunkating all before 'timemap/'
        req_path = req_path[tm_index:]
        try:
            if len(req_path.split(('/'), 2)) > 2:
                # gets the mime type for timemap (JSON or LINK)
                req_mime = req_path.split('/', 2)[1]
                # removes leading 'TIMEMAP_URI_PART/MIME_TYPE/'
                req_uri = req_path.split('/', 2)[2]
                return timemap(
                    req_uri,
                    req_mime,
                    start_response,
                    force_cache_refresh)
            else:
                raise TimegateError(
                    "Incomplete timemap request. \n"
                    "    Syntax: GET /timemap/:type/:resource", 400)
        except TimegateError as e:
            logging.info(
                "End of timemap request due to TimegateError : %s" % e)
            return error_response(e.status, start_response, e)
        except Exception as e:
            logging.critical(
                "End of timemap request due to an unhandled Exception : %s" %
                e)
            return error_response(503, start_response)

    # Unknown Service Request
    else:
        status = 400
        message = (
            "Service request does not contain '*/%s/<URI>' or '*/%s/<URI>'" % (
                TIMEMAP_URI_PART, TIMEGATE_URI_PART
            )
        )
        return error_response(status, start_response, message)


def error_response(status, start_response, message="Internal server error."):
    """Returns an error message to the user.

    :param status: HTTP Error Status.
    :param message: The error message string.
    :param start_response: WSGI callback function.
    :return: The HTTP body as a list of one element.
    """
    body = "%s \n %s \n" % (status, message)

    # Standard response header
    headers = [
        ('Date', nowstr()),
        ('Vary', 'accept-datetime'),
        ('Content-Length', str(len(body))),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close')
    ]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d Error: %s" % (status, message))
    return [body]


def memento_response(
        memento,
        uri_r,
        resource,
        start_response,
        first=None,
        last=None,
        has_timemap=False):
    """Returns a 302 redirection to the best Memento for a resource and a
    datetime requested by the user.

    :param memento: (The URI string, dt obj) of the best memento. :param
    uri_r: The original resource's complete URI :param resource: The
    original resource's shortened URI :param start_response: WSGI
    callback function :param first: (Optional) (URI string, dt obj) of
    the first memento :param last: (Optional) (URI string, dt obj) of
    the last memento :param has_timemap: Flag indicating that the
    handler accepts TimeMap requests too. Default True :return: The HTTP
    body as a list of one element

    """

    # Gather links containing original and if availible: TimeMap, first, last
    # TimeGate link not allowed here
    links = ['<%s>; rel="original"' % uri_r]
    if has_timemap and USE_TIMEMAPS:
        timemap_link = '%s/%s/%s/%s' % (PROTO_HOST, TIMEMAP_URI_PART,
                                        LINK_URI_PART, resource)
        timemap_json = '%s/%s/%s/%s' % (PROTO_HOST, TIMEMAP_URI_PART,
                                        JSON_URI_PART, resource)
        links.append('<%s>; rel="timemap"; type="application/link-format"' %
                     timemap_link)
        links.append('<%s>; rel="timemap"; type="application/json"' %
                     timemap_json)
    (uri_m, dt_m) = memento
    (uri_last, dt_last) = (uri_first, dt_first) = (None, None)
    if last:
        (uri_last, dt_last) = last
    if first:
        (uri_first, dt_first) = first
    if first and last and uri_first == uri_last:
        # There's only one memento (first = best = last)
        assert(uri_last == uri_m)
        links.append('<%s>; rel="first last memento"; datetime="%s"' %
                     (uri_m, date_str(dt_m)))
    else:
        if first:
            links.append('<%s>; rel="first memento"; datetime="%s"' %
                         (uri_first, date_str(dt_first)))
        if (uri_first != uri_m and uri_last != uri_m):
            # The best memento is neither the first nor the last
            links.append('<%s>; rel="memento"; datetime="%s"' %
                         (uri_m, date_str(dt_m)))
        if last:
            links.append('<%s>; rel="last memento"; datetime="%s"' %
                         (uri_last, date_str(dt_last)))

    # Builds the response headers
    status = 302
    headers = [
        ('Date', nowstr()),
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', uri_m),
        ('Link', ', '.join(links))
    ]
    body = []
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, Memento=%s for URI-R=%s" %
                 (status, uri_m, uri_r))
    return body


def timemap_link_response(mementos, uri_r, resource, start_response):
    """Returns a 200 TimeMap response.

    :param mementos: A sorted (ascending by date) list of (uri_str,
    datetime_obj) tuples representing a TimeMap :param uri_r: The URI-R
    of the original resource :param start_response: WSGI callback
    function :return: The HTTP body as a list of one element

    """
    assert len(mementos) >= 1

    # Adds Original, TimeGate and TimeMap links
    original_link = '<%s>; rel="original"' % uri_r
    timegate_link = '<%s/%s/%s>; rel="timegate"' % (
        PROTO_HOST, TIMEGATE_URI_PART, resource)
    link_self = '<%s/%s/%s/%s>; rel="self"; type="application/link-format"' % (
        PROTO_HOST, TIMEMAP_URI_PART, LINK_URI_PART, resource)
    json_self = '<%s/%s/%s/%s>; rel="timemap"; type="application/json"' % (
        PROTO_HOST, TIMEMAP_URI_PART, JSON_URI_PART, resource)

    # Browse through Mementos to generate the TimeMap links list
    mementos_links = [
        '<%s>; rel="memento"; datetime="%s"' %
        (uri, date_str(date)) for (
            uri, date) in mementos]

    # Sets up first and last relations
    if len(mementos_links) == 1:
        mementos_links[0] = mementos_links[0].replace(
            'rel="memento"', 'rel="first last memento"')
    else:
        mementos_links[0] = mementos_links[0].replace(
            'rel="memento"', 'rel="first memento"')
        mementos_links[-1] = mementos_links[-1].replace(
            'rel="memento"', 'rel="last memento"')

    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timegate_link, link_self, json_self]
    links.extend(mementos_links)
    body = ',\n'.join(links) + '\n'

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', nowstr()),
        ('Content-Length', str(len(body))),
        ('Content-Type', 'application/link-format'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, LINK TimeMap of size %d for URI-R=%s" %
                 (status, len(mementos), uri_r))

    return [body]


def timemap_json_response(mementos, uri_r, resource, start_response):
    """Creates and sends a timemap response.

    :param mementos: A sorted list of (uri_str, datetime_obj) tuples
    representing a timemap.
    :param uri_r: The URI-R of the original resource.
    :param start_response: WSGI callback function.
    :return: The HTTP body as a list of one element.
    """
    assert len(mementos) >= 1

    # Prepares the JSON response by building a dict
    response_dict = {}

    response_dict['original_uri'] = uri_r
    response_dict['timegate_uri'] = '%s/%s/%s' % (
        PROTO_HOST, TIMEGATE_URI_PART, resource)

    # Browse through Mementos to generate TimeMap links dict list
    mementos_links = [{'uri': urlstr, 'datetime': date_str(
        date)} for (urlstr, date) in mementos]

    # Builds up first and last links dict
    first_datestr = mementos[0][1].strftime(DATE_FORMAT)
    firstlink = {'uri': mementos[0][0], 'datetime': first_datestr}
    last_datestr = mementos[-1][1].strftime(DATE_FORMAT)
    lastlink = {'uri': mementos[-1][0], 'datetime': last_datestr}

    response_dict['mementos'] = {'last': lastlink,
                                 'first': firstlink,
                                 'list': mementos_links}

    # Builds self (TimeMap)links dict
    response_dict['timemap_uri'] = {
        'json_format': '%s/%s/%s/%s' % (PROTO_HOST, TIMEMAP_URI_PART,
                                        JSON_URI_PART, resource),
        'link_format': '%s/%s/%s/%s' % (PROTO_HOST, TIMEMAP_URI_PART,
                                        LINK_URI_PART, resource)
    }

    # Creates the JSON str from the dict
    response_json = json.dumps(response_dict)

    # Builds HTTP Response and WSGI return
    status = 200
    headers = [
        ('Date', nowstr()),
        ('Content-Length', str(len(response_json))),
        ('Content-Type', 'application/json'),
        ('Connection', 'close')]
    start_response(HTTP_STATUS[status], headers)
    logging.info("Returning %d, JSON TimeMap of size %d for URI-R=%s" %
                 (status, len(mementos), uri_r))
    return [response_json]


def get_and_cache(uri_r, getter, *args, **kwargs):
    """Uses the getter to retrieve a TimeMap for an original resource.

    The value is cached if the cache is activated.

    :param uri_r: The URI to retrieve and cache the TimeMap of.
    :param getter: Handler function to call.
    :param args: Arguments to pass to *getter*.
    :param kwargs: Keywords arguments to pass to *getter*.
    :return: The retrieved value.
    """
    if cache_activated:
        return cache.refresh(uri_r, getter, *args, **kwargs)
    else:
        return parsed_request(getter, *args, **kwargs)


def get_cached_timemap(uri_r, before=None):
    """Return a cached TimeMap for an original resource.

    It must span at least up to a certain date.

    :param uri_r: The original resource to look for.
    :param before: (Optional) datetime object until which a TimeMap suffice.
        If not given, the function will look for a complete TimeMap
        (complete with respect to the cache tolerance).
    :return: The cached TimeMap if it exists and is valid, None otherwise.
    """
    if cache_activated:
        if before:
            return cache.get_until(uri_r, before)
        else:
            return cache.get_all(uri_r)


def timegate(req_uri, req_datetime, start_response, force_cache_refresh=False):
    """Handles timegate high-level logic. Fetch the Memento for the requested
    URI at the requested date time. Returns a HTTP 302 response if it exists.
    If the resource handler allows batch requests, then the result may be
    cached.

    :param req_datetime: The Accept-Datetime string.
    :param req_uri: The requested original resource URI.
    :param start_response: WSGI callback function.
    :return: The body of the HTTP response.
    """

    logging.debug("TimeGate Request URI: %s" % req_uri)
    # Parses the date time and original resoure URI
    if req_datetime is None or req_datetime == '':
        accept_datetime = now()
    else:
        accept_datetime = validate_req_datetime(req_datetime, STRICT_TIME)

    resource = parse_req_resource(req_uri)
    # Rewrites the original URI from the requested resource
    uri_r = get_complete_uri(resource)
    # Runs the handler's API request for the Memento
    first = last = None
    if HAS_TIMEMAP:
        mementos = None
        if not force_cache_refresh:
            mementos = get_cached_timemap(uri_r, accept_datetime)
        if mementos is None:
            if HAS_TIMEGATE:
                logging.debug('Using single-request mode.')
                mementos = parsed_request(
                    handler.get_memento, uri_r, accept_datetime)
                # mementos, new_uri = parsed_request(handler.get_memento,
                #                                    uri_r, accept_datetime)
                # if new_uri:
                # uri_r = new_uri
                # There is more than one memento returned by get_memento.
                # Assume they are the first/last
                if len(mementos) > 1:
                    first = mementos[0]
                    if len(mementos) > 2:
                        last = mementos[-1]
            else:
                logging.debug('Using multiple-request mode.')
                mementos = get_and_cache(
                    uri_r, handler.get_all_mementos, uri_r)
                # mementos, new_uri = get_and_cache(
                #   uri_r, handler.get_all_mementos, uri_r)
                # if new_uri:
                # uri_r = new_uri
                first = mementos[0]
                last = mementos[-1]
        else:
            first = mementos[0]
            last = mementos[-1]
    else:
        mementos = parsed_request(handler.get_memento, uri_r, accept_datetime)
        # mementos, new_uri = parsed_request(handler.get_memento, uri_r,
        #                                    accept_datetime)
        # if new_uri:
        # uri_r = new_uri

        # There is more than one memento returned by get_memento. Assume they
        # are the first/last
        if len(mementos) > 1:
            first = mementos[0]
            if len(mementos) > 2:
                last = mementos[-1]

    # If the handler returned several Mementos, take the closest
    memento = best(mementos, accept_datetime, RESOURCE_TYPE)
    return memento_response(
        memento,
        uri_r,
        resource,
        start_response,
        first,
        last,
        has_timemap=HAS_TIMEMAP)


def timemap(req_uri, req_mime, start_response, force_cache_refresh=False):
    """Handles TimeMap high-level logic. Fetches all Mementos for an Original
    Resource and builds the TimeMap response. Returns a HTTP 200 response if it
    exists with the timemap in the message body.

    :param req_datetime: The Accept-Datetime string, if provided.
    :param req_uri: The requested original resource URI.
    :param start_response: WSGI callback function.
    :return: The body of the HTTP response.
    """
    if not (req_mime == JSON_URI_PART or req_mime == LINK_URI_PART):
        raise URIRequestError(
            'Mime type (%s) empty or unknown. Request must be '
            'GET timemap/%s/... or GET timemap/%s/... ' %
            (req_mime, JSON_URI_PART, LINK_URI_PART), 400)

    resource = parse_req_resource(req_uri)
    # Rewrites the original URI from the requested resource
    uri_r = get_complete_uri(resource)
    if HAS_TIMEMAP and USE_TIMEMAPS:
        mementos = None
        if not force_cache_refresh:
            mementos = get_cached_timemap(uri_r)
        if mementos is None:
            mementos = get_and_cache(uri_r, handler.get_all_mementos, uri_r)
            # mementos, new_uri = get_and_cache(
            #   uri_r, handler.get_all_mementos, uri_r)
            # if new_uri:
            # uri_r = new_uri
    elif not USE_TIMEMAPS:
        raise TimegateError("TimeMap requests are not supported.", 403)
    else:
        raise TimegateError("TimeMap requests are not supported", 403)

    # Generates the TimeMap response body and Headers
    if req_mime.startswith(JSON_URI_PART):
        return timemap_json_response(mementos, uri_r, resource, start_response)
    else:
        return timemap_link_response(mementos, uri_r, resource, start_response)
