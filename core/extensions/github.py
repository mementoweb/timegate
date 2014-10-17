import re
import logging

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError

class GitHubHandler(Handler):


    def __init__(self):
        # Mandatory fields
        self.resources = ['https://github.com/.+']
        self.singleonly = False

        # Local fields, the uri pattern of a resource
        # Here protocol, url, user, repo
        uri_re = '(https://)(github.com/)(.+/)(.+)'
        self.uri_rex = re.compile(uri_re)

        link_header_re = '<(.+?)>; rel="next"'
        self.header_rex = re.compile(link_header_re)


    # This example requires the datetime
    def getone(self, uri, datetime):
        # TODO this to lower the API requests
        raise NotImplementedError


    # This example requires the datetime
    def getall(self, uri):
        match = self.uri_rex.match(uri)
        assert bool(match)

        # URI deconstruction
        protocol = match.groups()[0]
        base = match.groups()[1]
        user = match.groups()[2]
        repo = match.groups()[3]

        # GitHub API parameters
        apibase = protocol+'api.'+base+'repos/'+user+repo+'/commits'
        params = {
            'per_page': 100,  # Max allowed is 100
        }
        auth=('MementoTimegate', 'LANLTimeGate14')
        cont = apibase  # Do not know if continue

        # Does sequential queries to get all revisions IDs and Timestamps
        queries_results = []
        while cont is not None:
            req = self.request(cont, params=params, auth=auth)
            if req.status_code == 404:
                raise HandlerError("Cannot find resource on version server.", 404)
            result = req.json()
            if 'message' in result:
                raise HandlerError(result['message'])
            if 'errors' in result:
                raise HandlerError(result['errors'])
            if len(result) > 0:
                # The request was successful
                queries_results += result
                # Search for possible continue
                if 'link' in req.headers:
                    link_header = req.headers['link']
                    headermatch = self.header_rex.search(link_header)
                    if bool(headermatch):
                        # The response was truncated, the rest can be obtained using
                        # the given "next" link
                        cont = headermatch.groups()[0]
                    else:
                        cont = None
                else:
                    cont = None

        # Processing list item
        def f(commit):
            return (commit['url'], commit['commit']['committer']['date'])

        return map(f, queries_results)

        #TODO API response if undefined.