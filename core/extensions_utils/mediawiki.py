import logging

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.timegateerrors import HandlerError

from tgutils import date_str


class MediaWikiHandler(Handler):



    def __init__(self):
        Handler.__init__(self)
        self.TIMESTAMPFMT = '%Y%m%d%H%M%S'

    # def getall(self, uri):
    #     params = {
    #         'rvlimit': 500,  # Max allowed
    #         'continue': ''  # The initial continue value is empty
    #     }
    #
    #     return self.query(uri, params)

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
      #  assert bool(match) not true in single request

        if not match:
            raise HandlerError('Not Found: Not a valid resource for this handler.', 404)

        base = match.groups()[0]
        resource = match.groups()[2]  # Note that anchors can be included

        # Mediawiki API parameters
        apibase = base+self.api_part
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
            try:
                result = req.json()
            except Exception as e:
                logging.error("No JSON can be decoded from API %s" % apibase)
                raise HandlerError("No API answer.", 404)
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
                if req_params['rvdir'] == 'older':
                    req_params['rvdir'] = 'newer'
                    return self.query(uri, req_params)
                else:
                    raise HandlerError("No revision returned from API.", 404)
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
            rev_uri = base + self.mementos_part + '?title=%s&oldid=%d' % (
                resource, rev['revid'])
            dt = rev['timestamp']
            return (rev_uri, dt)
        logging.debug("Returning API results of size %d" % len(queries_results))

        return map(f, queries_results)
