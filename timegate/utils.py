# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Various helper functions."""

from __future__ import absolute_import, print_function

import logging
from datetime import datetime, timedelta

from dateutil.parser import parse as parse_datestr
from dateutil.tz import tzutc

from ._compat import urlparse
from .errors import DateTimeError, URIRequestError


def get_complete_uri(resource, base_uri=None):
    """Return the complete URI from the resource.

    It appends the handler's base_uri to the resource if it not present.
    The purpose of this function is to allow more complex rewrite rules
    in the future.

    :param resource: The resource to make canonical.
    :param base_uri: Base URI.
    :return: The original URI in its canonical form.
    """
    if base_uri and not resource.startswith(base_uri):
        resource = base_uri + resource
    return resource


def parse_req_resource(pathstr):
    """Parse the requested URI string.

    Raises ``URIRequestError`` if the parse fails to recognize a valid URI.

    :param urlstr: A URI string, in a common format.
    :return: The URI string object.
    """
    try:
        # Replacing white spaces
        path = pathstr.replace(' ', '%20')
        # path = path.replace('&', '%26')
        uri = validate_uristr(path)
        logging.debug("Requested URI parsed to: " + uri)
        return uri
    except Exception as e:
        raise URIRequestError("Error: Cannot parse requested path '%s' \n"
                              "message: %s" % (pathstr, e))


def validate_uristr(uristr):
    """Control and validate the uri string.

    Raises an ``Exception`` if it is not valid.

    :param uristr: The uri string that needs to be verified.
    :return: The validated uri string.
    """
    return str(urlparse(uristr).geturl())


def validate_date(datestr, strict=False):
    """Control and validate the date string.

    :param datestr: The date string representation.
    :param strict: When True, the date must strictly follow the format defined
        in the config file (DATEFMT). When False, the date string can be fuzzy
        and the function will try to reconstruct it.
    :return: The datetime object form the parsed date string.
    """
    return parse_datestr(datestr, fuzzy=True).replace(tzinfo=tzutc())


def best(timemap, accept_datetime, timemap_type, sorted=True):
    """Find best memento."""
    assert(timemap)
    assert(accept_datetime)
    if timemap_type == 'vcs':
        return closest_before(timemap, accept_datetime, sorted)
    else:
        return closest(timemap, accept_datetime, sorted)


def closest(timemap, accept_datetime, sorted=True):
    """Find the absolutely closest memento chronologically to a datetime.

    Details of the requirements at
    http://www.mementoweb.org/guide/rfc/#SpecialCases, point 4.5.3.

    :param timemap: A sorted Timemap
    :param accept_datetime: the time object for which the best memento must
        be found.
    :param sorted: boolean to indicate if the list is sorted or not.
    :return: A tuple with memento URI and its datetime.
    """

    delta = timedelta.max
    memento_uri = None
    memento_dt = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dt)
        if diff <= delta:  # there can be several with the same datetime.
            memento_uri = url
            memento_dt = dt
            delta = diff
        elif sorted:
            # The list is sorted and the delta didn't increase this time.
            # It will not increase anymore: Return the Memento (best one).
            return (memento_uri, memento_dt)

    return (memento_uri, memento_dt)


def closest_before(timemap, accept_datetime, sorted=True):
    """Find the closest memento in the before a datetime.

    Details of the requirements at
    http://www.mementoweb.org/guide/rfc/#SpecialCases, point 4.5.3.

    :param timemap: A sorted Timemap.
    :param accept_datetime: The time object for which the best memento
        must be found.
    :param sorted: Boolean to indicate if the list is sorted or not.
    :return: The uri_m string of the closest memento.
    """

    delta = timedelta.max
    prev_uri = None
    prev_dt = None
    next_uri = None
    next_dt = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dt)
        if sorted:
            if dt > accept_datetime:
                if prev_uri is not None:
                    return (prev_uri, prev_dt)  # We passed 'accept-datetime'
                else:
                    # The first of the sorted list is already after the accept
                    # datetime
                    return (url, dt)
            prev_uri = url
            prev_dt = dt
        elif diff < delta:
            delta = diff
            if dt > accept_datetime:
                next_uri = url
                next_dt = dt
            else:
                prev_uri = url
                prev_dt = dt

    if prev_uri is not None:
        return (prev_uri, prev_dt)
    else:
        return (next_uri, next_dt)  # The first after accept datetime


def closest_binary(timemap, accept_datetime):
    """Finds the chronologically closest memento using binary search in a
    sorted list. Complexity O(log(n)) instead of O(n) Details of the
    requirements at http://www.mementoweb.org/guide/rfc/#SpecialCases, point
    4.5.3.

    :param timemap: A sorted Timemap.
    :param accept_datetime: The time object for which the best memento
        must be found.
    :return: The uri_m string of the closest memento.
    """
    # TODO implement


def closest_before_binary(timemap, accept_datetime):
    """Find the closest memento in the past of a datetime using binary search.

    Note the timemap **must** be a sorted list. Complexity ``O(log(n))``
    instead of ``O(n)`` Details of the requirements at
    http://www.mementoweb.org/guide/rfc/#SpecialCases, point 4.5.3.

    :param timemap: A sorted Timemap.
    :param accept_datetime: The time object for which the best memento
        must be found.
    :return: The uri_m string of the closest memento.
    """
    # TODO implement
