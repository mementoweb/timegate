import re
import logging

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError

from tgutils import date_str


class WikiHandler(Handler):


    def __init__(self):
        # Mandatory fields
        self.resources = ['https?://[a-z]{2,3}.wikipedia.org/wiki/.+']
        self.TIMESTAMPFMT = '%Y%m%d%H%M%S'

        # Local fields, the uri pattern of a resource
        uri_re = '(.+)(/wiki/)(.+)'
        self.rex = re.compile(uri_re)

    def getall(self, uri):
        params = {
            'rvlimit': 500,  # Max allowed
            'continue': ''  # The initial continue value is empty
        }

        return self.query(uri, params)

    # This example requires the datetime
    def getone(self, uri, accept_datetime):
        timestamp = date_str(accept_datetime, self.TIMESTAMPFMT)
        params = {
            'rvlimit': 1,  # Only need one
            'rvstart': timestamp,  # Start listing from here
            'rvdir': 'older'  # List in decreasing order
        }

        return self.query(uri, params)

        #TODO API response if undefined.

    def query(self, uri, req_params):
        match = self.rex.match(uri)
        assert bool(match)

        base = match.groups()[0]
        resource = match.groups()[2]  # Note that anchors can be included

        # Mediawiki API parameters
        apibase = base+'/w/api.php'
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'rvprop': 'ids|timestamp',
            'indexpageids': '',
            'titles': resource
        }
        params.update(req_params)

        # Does sequential queries to get all revisions IDs and Timestamps
        queries_results = []
        condition = True
        while condition:
            # Clone original request
            newparams = params.copy()
            req = self.request(apibase, params=newparams)
            if req.status_code == 404:
                raise HandlerError("Cannot find resource on version server.", 404)
            result = req.json()
            if 'error' in result:
                raise HandlerError(result['error'])
            if 'warnings' in result:
                logging.warn(result['warnings'])
            try: #TODO clean this
                # The request was successful
                pid = result['query']['pageids'][0]  # the JSON key of the page (only one)
                queries_results += result['query']['pages'][pid]['revisions']
                if ('missing' in result['query']['pages'][pid] or
                                'invalid' in result['query']['pages'][pid]):
                    raise HandlerError("Cannot find resource on version server.", 404)
            except Exception as e:
                raise HandlerError("Cannot find resource on version server.", 404)
            if 'continue' in result:
                # The response was truncated, the rest can be obtained using
                # &rvcontinue=ID
                cont = result['continue']
                # Modify it with the values returned in the 'continue' section of the last result.
                newparams.update(cont)
                condition = True
            else:
                condition = False

        # Processing list
        def f(rev):
            rev_uri = base + '/w/index.php?title=%s&oldid=%d' % (
                resource, rev['revid'])
            dt = rev['timestamp']
            return (rev_uri, dt)
        logging.debug("Returning API results of size %d" % len(queries_results))

        return map(f, queries_results)
