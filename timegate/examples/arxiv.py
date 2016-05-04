# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Arxiv handler."""

from __future__ import absolute_import, print_function

import logging
import re
from StringIO import StringIO

from lxml import etree

from timegate.errors import HandlerError
from timegate.handler import Handler


class ArxivHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

        # Resources

        # Ignores all that trails the identifier (? params, vX version,...)
        self.rex = re.compile(
            r'(http://arxiv.org)/((?:pdf)|(?:abs))/(\d+\.\d+)(.*)')
        self.api_base = 'http://export.arxiv.org/oai2'

    def get_all_mementos(self, uri_r):
        try:
            # Extract the resource ID
            match = self.rex.match(uri_r)
            if not match:
                raise HandlerError("URI does not match a valid resource.", 404)
            parts = match.groups()
            base = parts[0]
            type = parts[1]
            resource = parts[2]
            normalized_uri = '%s/%s/%s' % (base, type, resource)

            # Prepars the API call
            params = {
                'verb': 'GetRecord',
                'identifier': 'oai:arXiv.org:%s' % resource,
                'metadataPrefix': 'arXivRaw'
            }

            # Queries the API and extract the values
            response = self.request(self.api_base, params=params)
            if not response:
                raise HandlerError("API response not 2XX", 404)
            root = etree.parse(StringIO(response.content),
                               etree.XMLParser(recover=True))
            versions = root.findall(
                './/{http://arxiv.org/OAI/arXivRaw/}version')

            # Processes the return
            def mapper(version):
                v = version.xpath('@*')[0]
                date = version.find(
                    './{http://arxiv.org/OAI/arXivRaw/}date').text
                return (normalized_uri + v, date)

            return map(mapper, versions)

        except HandlerError as he:
            raise he

        except Exception as e:
            logging.error('Arxiv handler exception: %s returning 404' % e)
            return
