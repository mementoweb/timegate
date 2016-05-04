# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2016 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""Greece handler."""

import logging
import re
import urllib

from timegate.errors import HandlerError
from timegate.handler import Handler


class GreeceHandler(Handler):

    def __init__(self):

        self.baseuri = "http://83.212.204.92:8080/*/"

        regex = r'<a onclick="SetAnchorDate\(\'.*\'\);" href="http://83.212.204.92:8080/[\S]*">';
        self.uriRegex = re.compile(regex)
        Handler.__init__(self)

    def get_all_mementos(self, req_url):
        # def fetch_changes(self, req, requri, dt=None):
        # implement the changes list for this particular proxy

        uri = self.baseuri + req_url
        try:
            fh = urllib.urlopen(uri)
        except Exception as e:
            logging.error("Couldn't retrieve data from %s : %s" % (uri, str(e)))
            return None
        data = fh.read()
        fh.close()

        changes = []
        uris = re.findall(self.uriRegex, data)
        for u in uris:
            dtstr = u[27:41]
            loc = u[52:-2]
            dtstr += " GMT"
            # dtobj = dateparser.parse(dtstr)
            changes.append((loc, dtstr))

        return changes
