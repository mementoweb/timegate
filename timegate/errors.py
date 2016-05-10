# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Custom TimeGate errors."""

from __future__ import absolute_import, print_function

from werkzeug.exceptions import HTTPException


class TimegateError(HTTPException):
    """General TimeGate Exception."""

    code = 400
    description = 'Invalid TimeGate request.'

    def __init__(self, msg, status=None):
        super(TimegateError, self).__init__(description=msg)
        if status:
            self.code = status


class TimeoutError(TimegateError):
    """Raise to signalize a timeout."""

    code = 416


class URIRequestError(TimegateError):
    """Raise if the request contains invalid URI."""

    code = 400


class HandlerError(TimegateError):
    """Raise to signal handler error."""

    code = 503


class DateTimeError(TimegateError):
    """Raise if the server is unable to handle the date time."""

    code = 400


class CacheError(TimegateError):
    """Raise if the cache is not functioning."""

    code = 500
