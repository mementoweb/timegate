# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2014, 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Memento proxy for Estonia Web Archive.

TODO: rewrite regex html parsing(?) with lxml.
"""

from __future__ import absolute_import, print_function

import logging
import re

from timegate.errors import HandlerError
from timegate.handler import Handler

BASEURI = "http://veebiarhiiv.digar.ee/a/*/"


class EsHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        regex = r'<a onclick="SetAnchorDate\(\'(.*)\'\);" href="(.*)">'
        self.uriRegex = re.compile(regex)

    def get_all_mementos(self, req_url):
        # implement the changes list for this particular proxy

        uri = BASEURI + req_url
        try:
            resp = self.request(uri)
            data = resp.content
        except Exception as e:
            logging.error("Cannot request URI: %s" % e)
            raise HandlerError("Cannot request URI", 404)

        changes = []
        uris = re.findall(self.uriRegex, data)
        for u in uris:
            dtstr = u[0]
            loc = u[1]
            dtstr += " GMT"
            changes.append((loc, dtstr))

        return changes
