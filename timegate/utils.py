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


def validate_uristr(uristr):
    """Control and validate the uri string.

    Raises an ``Exception`` if it is not valid.

    :param uristr: The uri string that needs to be verified.
    :return: The validated uri string.
    """
    if uristr is None:
        raise ValueError('URI can not be None')
    return str(urlparse(uristr).geturl())


def validate_date(datestr):
    """Control and validate the date string.

    :param datestr: The date string representation.
    :return: The datetime object form the parsed date string.
    """
    return parse_datestr(datestr, fuzzy=True).replace(tzinfo=tzutc())


def best(timemap, accept_datetime, timemap_type):
    """Find best memento."""
    assert(timemap)
    assert(accept_datetime)
    if timemap_type == 'vcs':
        return closest_before(timemap, accept_datetime)
    else:
        return closest(timemap, accept_datetime)


def closest(timemap, accept_datetime):
    """Find the absolutely closest memento chronologically to a datetime.

    Details of the requirements at
    http://www.mementoweb.org/guide/rfc/#SpecialCases, point 4.5.3.

    :param timemap: A sorted Timemap
    :param accept_datetime: the time object for which the best memento must
        be found.
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
        else:
            # The list is sorted and the delta didn't increase this time.
            # It will not increase anymore: Return the Memento (best one).
            return (memento_uri, memento_dt)

    return (memento_uri, memento_dt)


def closest_before(timemap, accept_datetime):
    """Find the closest memento in the before a datetime.

    Details of the requirements at
    http://www.mementoweb.org/guide/rfc/#SpecialCases, point 4.5.3.

    :param timemap: A sorted Timemap.
    :param accept_datetime: The time object for which the best memento
        must be found.
    :return: The uri_m string of the closest memento.
    """
    prev_uri = prev_dt = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dt)
        if dt > accept_datetime:
            if prev_uri is not None:
                return (prev_uri, prev_dt)  # We passed 'accept-datetime'
            else:
                # The first of the sorted list is already after the accept
                # datetime
                return (url, dt)
        prev_uri = url
        prev_dt = dt

    return (prev_uri, prev_dt)


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
