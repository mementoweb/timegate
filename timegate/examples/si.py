# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2015 LANL.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""TimeGate proxy for uni-lj.si."""

from __future__ import absolute_import, print_function

import logging
import re
import urllib

from timegate.handler import Handler


class SloveniaHandler(Handler):

    def __init__(self):
        self.baseuri = "http://nukrobi2.nuk.uni-lj.si:8080/wayback/*/"
        regex = r'<a onclick="SetAnchorDate\(\'.*\'\);" href="http://nukrobi2.nuk.uni-lj.si:8080/wayback/[\S]*">'
        self.uriRegex = re.compile(regex)
        Handler.__init__(self)

    def get_all_mementos(self, req_url):
        # def fetch_changes(self, req, requri, dt=None):
        # implement the changes list for this particular proxy

        uri = self.baseuri + req_url
        try:
            fh = urllib.urlopen(uri)
        except Exception as e:
            logging.error("Couldn't retrieve data from %s : %s" %
                          (uri, str(e)))
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
