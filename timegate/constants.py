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

from __future__ import absolute_import, print_function

import logging
import os
from configparser import ConfigParser

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
# URI parts
TIMEMAP_URI_PART = 'timemap'
TIMEGATE_URI_PART = 'timegate'

# Memento date rfc1123
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

# Timemaps types and URI parts
MIME_TYPE_JSON = 'application/json'
MIME_TYPE_LINK = 'application/link-format'

JSON_URI_PART = 'json'
LINK_URI_PART = 'link'

# Default handler location
EXTENSIONS_PATH = 'core/handler/'

# Logging
LOG_FORMAT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'
logging.basicConfig(filemode='w', format=LOG_FORMAT, level=logging.DEBUG)
logging.getLogger('uwsgi').setLevel(logging.WARNING)

# TimeMap max size (in URIs) safeguard
TM_MAX_SIZE = 100000


# Configuration constants
conf = ConfigParser()
with open(os.path.join(os.path.dirname(__file__), 'conf', 'config.ini')) as f:
    conf.read_file(f)

# Server configuration
HOST = conf.get('server', 'host').rstrip('/')
if HOST == '':
    msg = (
        "Empty host name. TimeGate will not work properly. "
        "Please edit conf/config.ini file to add "
        "the TimeGate's host location.")
    logging.critical(msg)
    raise Exception(msg)

STRICT_TIME = True  # conf.getboolean('server', 'strict_datetime')
API_TIME_OUT = conf.getfloat('server', 'api_time_out')

# Handler configuration
HANDLER_MODULE = None
BASE_URI = ''
if conf.has_option('handler', 'handler_class'):
    HANDLER_MODULE = conf.get('handler', 'handler_class')
if conf.has_option('handler', 'base_uri'):
    BASE_URI = conf.get('handler', 'base_uri')
if conf.getboolean('handler', 'is_vcs'):
    RESOURCE_TYPE = 'vcs'
else:
    RESOURCE_TYPE = 'snapshot'

if conf.has_option('handler', 'use_timemap'):
    USE_TIMEMAPS = conf.getboolean('handler', 'use_timemap')
else:
    USE_TIMEMAPS = False

# Cache
# When False, all cache requests will be cache MISS
CACHE_USE = conf.getboolean('cache', 'cache_activated')
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = conf.getint('cache', 'cache_refresh_time')
# Cache files paths
CACHE_DIRECTORY = conf.get('cache', 'cache_directory').rstrip('/')
# Maximum number of TimeMaps stored in cache
CACHE_MAX_VALUES = conf.getint('cache', 'cache_max_values')
# Cache files paths
CACHE_FILE = CACHE_DIRECTORY  # + '/cache_data'
# Cache expiration (space bound) in seconds
CACHE_EXP = 259200  # Three days

logging.info("Configuration loaded with success.")
