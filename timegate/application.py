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

import json
import logging
import os
from datetime import datetime

from dateutil.tz import tzutc
from link_header import Link, LinkHeader
from pkg_resources import iter_entry_points
from werkzeug.exceptions import HTTPException, abort
from werkzeug.http import http_date, parse_date
from werkzeug.local import Local, LocalManager
from werkzeug.routing import BaseConverter, Map, Rule, ValidationError
from werkzeug.utils import cached_property, import_string
from werkzeug.wrappers import Request, Response

from . import constants
from .cache import Cache
from .config import Config
from .handler import Handler, parsed_request
from .utils import best

local = Local()
"""Thread safe local data storage."""

local_manager = LocalManager([local])
"""Manager for local data storage."""

request = local('request')
"""Proxy to request object."""

# logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)


def url_for(*args, **kwargs):
    """Proxy to URL Map adapter builder."""
    return request.adapter.build(*args, **kwargs)


def load_handler(name_or_path):
    """Load handler from entry points or import string."""
    if isinstance(name_or_path, Handler):
        return name_or_path

    handlers = list(iter_entry_points('timegate.handlers', name=name_or_path))
    number_of_handlers = len(handlers)
    if number_of_handlers > 1:
        raise RuntimeError(
            'Multiple handlers with the same name "{0}" has been found'.format(
                name_or_path
            )
        )
    elif number_of_handlers == 1:
        return handlers[0].load()()
    else:
        return import_string(name_or_path)()


class URIConverter(BaseConverter):
    """URI Converter."""

    def __init__(self, url_map, base_uri=None):
        super(URIConverter, self).__init__(url_map)
        self.base_uri = base_uri
        self.regex = (
            r"([^:/?#]+:)?(//[^/?#]*)?"
            r"[^?#]*(\?[^#]*)?(#.*)?"
        )

    def to_python(self, value):
        """Return value with base URI prefix."""
        value = value.replace(' ', '%20')  # encode
        if self.base_uri and not value.startswith(self.base_uri):
            return self.base_uri + value
        return value

    def to_url(self, value):
        """Return value without base URI if it is defined."""
        value = value.replace('%20', ' ')  # decode
        if self.base_uri and value.startswith(self.base_uri):
            return value[len(self.base_uri):]
        return value


class TimeGate(object):
    """Implementation of Memento protocol with configurable handlers."""

    def __init__(self, config=None, cache=None):
        """Initialize application with handler."""
        self.config = Config(None)
        self.config.from_object(constants)
        self.config.update(config or {})
        self.cache = None
        if cache:
            self.cache = cache
        elif self.config['CACHE_USE']:
            self._build_default_cache()

    @cached_property
    def handler(self):
        handler = load_handler(self.config['HANDLER_MODULE'])
        HAS_TIMEGATE = hasattr(handler, 'get_memento')
        HAS_TIMEMAP = hasattr(handler, 'get_all_mementos')
        if self.config['USE_TIMEMAPS'] and (not HAS_TIMEMAP):
            logging.error(
                "Handler has no get_all_mementos() function "
                "but is suppose to serve timemaps.")

        if not (HAS_TIMEGATE or HAS_TIMEMAP):
            raise NotImplementedError(
                "NotImplementedError: Handler has neither `get_memento` "
                "nor `get_all_mementos` method.")
        return handler

    @cached_property
    def url_map(self):
        """Build URL map."""
        base_uri = self.config['BASE_URI']
        rules = [
            Rule('/timegate/<uri(base_uri="{0}"):uri_r>'.format(base_uri),
                 endpoint='timegate', methods=['GET', 'HEAD']),
            Rule('/timemap/<any(json, link):response_type>/'
                 '<uri(base_uri="{0}"):uri_r>'.format(base_uri),
                 endpoint='timemap', methods=['GET', 'HEAD']),
        ]
        return Map(rules, converters={'uri': URIConverter})

    def _build_default_cache(self):
        """Build default cache object."""
        self.cache = Cache(
            self.config['CACHE_FILE'],
            self.config['CACHE_TOLERANCE'],
            self.config['CACHE_EXP'],
            self.config['CACHE_MAX_VALUES'],
        )

    def __repr__(self):
        """Representation of this class."""
        return '<{0} {1}>'.format(
            self.__class__.__name__, self.handler.__class__.__name__
        )

    def dispatch_request(self, request):
        """Choose correct method."""
        request.adapter = adapter = self.url_map.bind_to_environ(
            request.environ
        )
        try:
            endpoint, values = adapter.match()
            return getattr(self, endpoint)(**values)
        except HTTPException as e:
            return e
        finally:
            self.adapter = None

    def wsgi_app(self, environ, start_response):
        local.request = request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        """Handle a request."""
        return self.wsgi_app(environ, start_response)

    def get_memento(self, uri_r, accept_datetime):
        """Return a URL-M for an original resource.

        It must span at least up to a certain date.

        :param uri_r: The original resource to look for.
        :param accept_datetime: Datetime object with requested time.
        :return: The TimeMap if it exists and is valid.
        """
        return parsed_request(self.handler.get_memento,
                              uri_r, accept_datetime)

    def get_all_mementos(self, uri_r):
        """Uses the handler to retrieve a TimeMap for an original resource.

        The value is cached if the cache is activated.

        :param uri_r: The URI to retrieve and cache the TimeMap of.
        :return: The retrieved value.
        """
        mementos = None
        if self.cache and request.cache_control != 'no-cache':
            mementos = self.cache.get_all(uri_r)
        if mementos is None:
            mementos = parsed_request(self.handler.get_all_mementos, uri_r)
            if self.cache:
                self.cache.set(uri_r, mementos)
        return mementos

    def timegate(self, uri_r):
        """Handle timegate high-level logic.

        Fetch the Memento for the requested URI at the requested date time.
        Returns a HTTP 302 response if it exists.  If the resource handler
        allows batch requests, then the result may be cached.

        :return: The body of the HTTP response.
        """
        if 'Accept-Datetime' in request.headers:
            accept_datetime = parse_date(
                request.headers['Accept-Datetime']
            ).replace(tzinfo=tzutc())
        else:
            accept_datetime = datetime.utcnow().replace(tzinfo=tzutc())

        # Runs the handler's API request for the Memento
        mementos = first = last = None
        HAS_TIMEMAP = hasattr(self.handler, 'get_all_mementos')
        if HAS_TIMEMAP and self.config['USE_TIMEMAPS']:
            logging.debug('Using multiple-request mode.')
            mementos = self.get_all_mementos(uri_r)

        if mementos:
            first = mementos[0]
            last = mementos[-1]
            memento = best(mementos, accept_datetime,
                           self.config['RESOURCE_TYPE'])
        else:
            logging.debug('Using single-request mode.')
            memento = self.get_memento(uri_r, accept_datetime)

        # If the handler returned several Mementos, take the closest
        return memento_response(
            memento,
            uri_r,
            first,
            last,
            has_timemap=HAS_TIMEMAP and self.config['USE_TIMEMAPS'],
        )

    def timemap(self, uri_r, response_type='link'):
        """Handle TimeMap high-level logic.

        It fetches all Mementos for an Original Resource and builds the TimeMap
        response. Returns a HTTP 200 response if it exists with the timemap in
        the message body.

        :param req_uri: The requested original resource URI.
        :param start_response: WSGI callback function.
        :return: The body of the HTTP response.
        """
        if not self.config['USE_TIMEMAPS']:
            abort(403)

        mementos = self.get_all_mementos(uri_r)
        # Generates the TimeMap response body and Headers
        if response_type == 'json':
            return timemap_json_response(self, mementos, uri_r)
        else:
            return timemap_link_response(self, mementos, uri_r)


@local_manager.middleware
def application(environ, start_response):
    """WSGI application object.

    This is the start point of the TimeGate server.

    TimeMap requests are parsed here.

    :param environ: Dictionary containing environment variables from
    the client request.
    :param start_response: Callback function used to send HTTP status
    and headers to the server.
    :return: The response body, in a list of one str element.
    """
    app = TimeGate()
    app.config.from_inifile(
        os.path.join(os.path.dirname(__file__), 'conf', 'config.ini')
    )
    return app(environ, start_response)


def memento_response(
        memento,
        uri_r,
        first=None,
        last=None,
        has_timemap=False):
    """Return a 302 redirection to the best Memento for a resource.

    It includes necessary headers including datetime requested by the user.

    :param memento: (The URI string, dt obj) of the best memento.
    :param uri_r: The original resource's complete URI.
    :param first: (Optional) (URI string, dt obj) of the first memento.
    :param last: (Optional) (URI string, dt obj) of the last memento.
    :param has_timemap: Flag indicating that the handler accepts
        TimeMap requests too. Default True.
    :return: The ``Response`` object.
    """
    # Gather links containing original and if availible: TimeMap, first, last
    # TimeGate link not allowed here
    links = [Link(uri_r, rel='original')]
    if has_timemap:
        for response_type, mime in (('link', 'application/link-format'),
                                    ('json', 'application/json'), ):
            links.append(Link(
                url_for('timemap', dict(
                    response_type=response_type, uri_r=uri_r
                ), force_external=True),
                rel='timemap', type=mime
            ))

    (uri_m, dt_m) = memento
    (uri_last, dt_last) = (uri_first, dt_first) = (None, None)
    if last:
        (uri_last, dt_last) = last
    if first:
        (uri_first, dt_first) = first
    if first and last and uri_first == uri_last:
        # There's only one memento (first = best = last)
        assert(uri_last == uri_m)
        links.append(Link(uri_m, rel='first last memento',
                          datetime=http_date(dt_m)))
    else:
        if first:
            links.append(Link(uri_m, rel='first memento',
                              datetime=http_date(dt_first)))
        if (uri_first != uri_m and uri_last != uri_m):
            # The best memento is neither the first nor the last
            links.append(Link(uri_m, rel='memento',
                              datetime=http_date(dt_m)))
        if last:
            links.append(Link(uri_m, rel='last memento',
                              datetime=http_date(dt_last)))

    # Builds the response headers
    headers = [
        ('Date', http_date(datetime.utcnow())),
        ('Vary', 'accept-datetime'),
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('Connection', 'close'),
        ('Location', uri_m),
        ('Link', str(LinkHeader(links))),
    ]
    return Response(None, headers=headers, status=302)


def timemap_link_response(app, mementos, uri_r):
    """Return a 200 TimeMap response.

    :param mementos: A sorted (ascending by date) list of (uri_str,
    datetime_obj) tuples representing a TimeMap.
    :param uri_r: The URI-R of the original resource.
    :return: The ``Response`` object.
    """
    assert len(mementos) >= 1

    # Adds Original, TimeGate and TimeMap links
    original_link = Link(uri_r, rel='original')
    timegate_link = Link(
        url_for('timegate', dict(uri_r=uri_r), force_external=True),
        rel='timegate',
    )
    link_self = Link(
        url_for('timemap', dict(
            response_type='link', uri_r=uri_r
        ), force_external=True),
        rel='self', type='application/link-format',
    )
    json_self = Link(
        url_for('timemap', dict(
            response_type='json', uri_r=uri_r
        ), force_external=True),
        rel='timemap', type='application/json',
    )

    # Sets up first and last relations
    if len(mementos) == 1:
        mementos_links = [Link(mementos[0][0], rel='first last memento',
                               datetime=http_date(mementos[0][1]))]
    else:
        # Browse through Mementos to generate the TimeMap links list
        mementos_links = [
            Link(mementos[0][0], rel='first memento',
                 datetime=http_date(mementos[0][1]))
        ] + [
            Link(uri, rel='memento', datetime=http_date(date))
            for (uri, date) in mementos[1:-1]
        ] + [
            Link(mementos[-1][0], rel='last memento',
                 datetime=http_date(mementos[-1][1]))
        ]

    # Aggregates all link strings and constructs the TimeMap body
    links = [original_link, timegate_link, link_self, json_self]
    links.extend(mementos_links)
    body = ',\n'.join([str(l) for l in links]) + '\n'

    # Builds HTTP Response and WSGI return
    headers = [
        ('Date', http_date(datetime.utcnow())),
        ('Content-Length', str(len(body))),
        ('Content-Type', 'application/link-format'),
        ('Connection', 'close'),
    ]
    return Response(body, headers=headers)


def timemap_json_response(app, mementos, uri_r):
    """Creates and sends a timemap response.

    :param mementos: A sorted list of (uri_str, datetime_obj) tuples
    representing a timemap.
    :param uri_r: The URI-R of the original resource.
    :param start_response: WSGI callback function.
    :return: The ``Response`` object.
    """
    assert len(mementos) >= 1

    # Prepares the JSON response by building a dict
    response_dict = {}

    response_dict['original_uri'] = uri_r
    response_dict['timegate_uri'] = url_for(
        'timegate', dict(uri_r=uri_r), force_external=True
    )

    # Browse through Mementos to generate TimeMap links dict list
    mementos_links = [
        {'uri': urlstr, 'datetime': http_date(date)}
        for (urlstr, date) in mementos
    ]

    # Builds up first and last links dict
    firstlink = {'uri': mementos[0][0], 'datetime': http_date(mementos[0][1])}
    lastlink = {'uri': mementos[-1][0], 'datetime': http_date(mementos[-1][1])}

    response_dict['mementos'] = {
        'last': lastlink,
        'first': firstlink,
        'list': mementos_links,
    }

    # Builds self (TimeMap)links dict
    response_dict['timemap_uri'] = {
        'json_format': url_for('timemap', dict(
            response_type='json', uri_r=uri_r
        ), force_external=True),
        'link_format': url_for('timemap', dict(
            response_type='link', uri_r=uri_r
        ), force_external=True),
    }

    # Creates the JSON str from the dict
    response_json = json.dumps(response_dict)

    # Builds HTTP Response and WSGI return
    headers = [
        ('Date', http_date(datetime.utcnow())),
        ('Content-Length', str(len(response_json))),
        ('Content-Type', 'application/json'),
    ]
    return Response(response_json, headers=headers)
