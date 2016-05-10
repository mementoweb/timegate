# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Important constants of the TimeGate server."""

# Code constants
HTTP_STATUS = {
    200: "200 OK",
    302: "302 Found",
    400: "400 Bad Request",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    416: '416 Requested Range Not Satisfiable',
    500: "500 Internal Server Error",
    502: "502 Bad Gateway",
    501: "501 Not Implemented",
    503: "503 Service Unavailable"
}

# Memento date rfc1123
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

# TimeMap max size (in URIs) safeguard
TM_MAX_SIZE = 100000

# Server configuration
HOST = None
STRICT_TIME = True
API_TIME_OUT = 6

# Handler configuration
HANDLER_MODULE = 'simple'
BASE_URI = ''
RESOURCE_TYPE = 'snapshot'
USE_TIMEMAPS = True

# Cache
# When False, all cache requests will be cache MISS
CACHE_USE = False
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = 86400
# Cache files paths
CACHE_DIRECTORY = 'cache'
# Maximum number of TimeMaps stored in cache
CACHE_MAX_VALUES = 250
# Cache files paths
CACHE_FILE = CACHE_DIRECTORY  # + '/cache_data'
# Cache expiration (space bound) in seconds
CACHE_EXP = 259200  # Three days
