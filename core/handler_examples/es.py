"""
Memento proxy for Estonia Web Archive
TODO: rewrite regex html parsing(?) with lxml
"""
import logging

import re

from core.handler_baseclass import Handler
from errors.timegateerrors import HandlerError


__author__ = "aalsum, Yorick Chollet"

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
            logging.error("Cannot request URI: %s" % e.message)
            raise HandlerError("Cannot request URI", 404)

        changes = []
        uris = re.findall(self.uriRegex, data)
        for u in uris:
            dtstr = u[0]
            loc = u[1]
            dtstr += " GMT"
            changes.append((loc, dtstr))

        return changes