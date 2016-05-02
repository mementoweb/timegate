
import urllib
import logging

import re

from core.handler_baseclass import Handler
from errors.timegateerrors import HandlerError


__author__ = "Yorick, Luda"


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
