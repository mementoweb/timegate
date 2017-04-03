# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Implement default configuration and custom loaders."""

from __future__ import absolute_import, print_function

from configparser import ConfigParser

from ._compat import string_types


class Config(dict):
    """Implement custom loaders to populate dict."""

    _instance = None

    def __new__(cls, root_path, defaults=None):
        """
        Converting this into a singleton for cached access.
        :param root_path: 
        :param defaults: 
        :return: 
        """
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, root_path, defaults=None):
        """
        Build an empty config wrapper.

        :param root_path: Path to which files are read relative from.
        :param defaults: An optional dictionary of default values.
        """
        dict.__init__(self, defaults or {})
        self.root_path = root_path

    def from_inifile(self, filename, silent=True):
        """Update the values in the config from an INI file."""
        conf = ConfigParser()
        with open(filename) as f:
            conf.read_file(f)

        # Server configuration
        self['HOST'] = conf.get('server', 'host').rstrip('/')
        self['USER_AGENT'] = conf.get('server', 'user_agent')
        self['STRICT_TIME'] = conf.getboolean('server', 'strict_datetime')
        if conf.has_option('server', 'api_time_out'):
            self['API_TIME_OUT'] = conf.getfloat('server', 'api_time_out')

        # Handler configuration
        if conf.has_option('handler', 'handler_class'):
            self['HANDLER_MODULE'] = conf.get('handler', 'handler_class')
        if conf.has_option('handler', 'base_uri'):
            self['BASE_URI'] = conf.get('handler', 'base_uri')
        if conf.getboolean('handler', 'is_vcs'):
            self['RESOURCE_TYPE'] = 'vcs'
        else:
            self['RESOURCE_TYPE'] = 'snapshot'

        if conf.has_option('handler', 'use_timemap'):
            self['USE_TIMEMAPS'] = conf.getboolean('handler', 'use_timemap')
        else:
            self['USE_TIMEMAPS'] = False

        # Cache
        # When False, all cache requests will be cache MISS
        self['CACHE_USE'] = conf.getboolean('cache', 'cache_activated')
        # Time window in which the cache value is considered young
        # enough to be valid
        self['CACHE_TOLERANCE'] = conf.getint('cache', 'cache_refresh_time')
        # Cache files paths
        self['CACHE_DIRECTORY'] = conf.get(
            'cache', 'cache_directory').rstrip('/')
        # Maximum number of TimeMaps stored in cache
        self['CACHE_MAX_VALUES'] = conf.getint('cache', 'cache_max_values')
        # Cache files paths
        self['CACHE_FILE'] = self['CACHE_DIRECTORY']  # + '/cache_data'

    def from_object(self, obj):
        """Update config with values from given object.

        :param obj: An import name or object.
        """
        if isinstance(obj, string_types):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)
