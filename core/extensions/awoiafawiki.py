import re
import logging

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError


class AWOIAFHandler(Handler):


    def __init__(self):
        # Mandatory fields
        self.resources = ['http://awoiaf.westeros.org/index.php/.+']  # TODO parametrize
        self.single_requests = False
        self.batch_requests = True

        # Local fields, the uri pattern of a resource
        uri_re = '(.+)(/index.php/)(.+)'  # TODO parametrize
        self.rex = re.compile(uri_re)


    # This example requires the datetime
    def getall(self, uri):
        match = self.rex.match(uri)
        assert bool(match)

        base = match.groups()[0]   # TODO parametrize
        resource = match.groups()[2]  # Note that anchors can be included

        # Mediawiki API parameters
        apibase = base+'/api.php'  # TODO parametrize
        params = {
            'action': 'query',
            'format': 'json',
            'prop': 'revisions',
            'rvprop': 'ids|timestamp',
            'rvlimit': 500,  # Max allowed is 500
            'indexpageids': '',
            'titles': resource
        }
        cont = {'continue': ''}  # The initial continue value is empty

        # Does sequential queries to get all revisions IDs and Timestamps
        queries_results = []
        while cont is not None:
            # Clone original request
            newparams = params.copy()
            # Modify it with the values returned in the 'continue' section of the last result.
            newparams.update(cont)
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
            else:
                cont = None

        # Processing list
        def f(rev):
            rev_uri = base + '/index.php?title=%s&oldid=%d' % (
                resource, rev['revid'])
            dt = rev['timestamp']
            return (rev_uri, dt)

        return map(f, queries_results)

        #TODO API response if undefined.