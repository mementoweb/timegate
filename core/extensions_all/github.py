import re

__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.timegateerrors import HandlerError

import time

ACCEPTABLE_RESOURCE = """Acceptable resources URI:
repositories (github.com/:user/:repo/),
folders (github.com/:user/:repo/trees/:path),
files (github.com/:user/:repo/blob/:path)
and raw files (raw.githubusercontent.com/:user/:repo/master/:path)"""


class GitHubHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        # Mandatory fields
        self.resources = ['https://github.com/.+',
                          'https://raw.githubusercontent.com/']

        # Local fields
        self.api = 'https://api.github.com'

        # Precompiles regular expressions
        self.rex = re.compile("""  # The format of URI-Rs
                              (https://)  # protocol
                              ((?:raw.githubusercontent|github).com/)  # base
                              ([^/]+)/  # user
                              ([^/]+)  # repo
                              (/.+)?  # optional path
                              """, re.X)  # verbosed: ignore whitespaces and \n
        self.header_rex = re.compile('<(.+?)>; rel="next"')  # The regex for the query continuation header
        self.file_rex = re.compile('(/blob)?/master')  # The regex for files

    def get_all_mementos(self, uri):
        MAX_TIME = 20 #seconds

        # URI deconstruction
        match = self.rex.match(uri)
        if not bool(match):
            raise HandlerError("Github uri does not match a valid resource. \n"
                               + ACCEPTABLE_RESOURCE, 404)
        protocol = match.groups()[0]
        base = match.groups()[1]
        user = match.groups()[2]
        repo = match.groups()[3]
        req_path = match.groups()[4]

        # GitHub API parameters
        # Todo get commit url from api page...

        # Defining Resource type and response handling
        if req_path is None or req_path.startswith('/tree/master'):
            if req_path:
                path = req_path.replace('/tree/master', '', 1)
            else:
                path = '/'

            # Resource is a directory
            def repo_tupler(commit):
                return (commit['html_url']+'?path='+path,
                        commit['commit']['committer']['date'])

            mapper = repo_tupler

        elif bool(self.file_rex.match(req_path)):
                # Resource is a file
                path = req_path.replace('/blob', '', 1).replace('/master', '', 1)

                def file_tupler(commit):
                    if base == 'github.com/':
                        # HTML Resource
                        memento_path = '/blob/%s%s' % (
                            commit['sha'], path)
                    else:
                        # Raw Resource
                        if path == '' or path.endswith('/'):
                            raise HandlerError("'%s' not found: \n"
                                            "Raw resource must be a file." %
                                            path, 404)
                        memento_path = '/%s%s' % (
                            commit['sha'], path)

                    uri_m = '%s%s%s/%s%s' % (
                        protocol, base, user, repo, memento_path)
                    return (uri_m, commit['commit']['committer']['date'])

                mapper = file_tupler

        else:
            # The resource is neither a file nor a directory.
            raise HandlerError("GitHub resource type not found."
                               + ACCEPTABLE_RESOURCE, 404)

        # Initiating request variables
        apibase = '%s/repos/%s/%s/commits' % (self.api, user, repo)
        params = {
            'per_page': 100,  # Max allowed is 100
            'path': str(path)
        }
        auth = ('MementoTimegate', 'LANLTimeGate14')
        cont = apibase  # The first continue is the beginning

        # Does sequential queries to get all commits of the particular resource
        queries_results = []
        tmax = int(time.time()) + MAX_TIME
        while cont is not None:
            if int(time.time()) > tmax:
                raise HandlerError("Resource too big to be served. GitHub Handler TimeOut (timeout: %d seconds)" % MAX_TIME, 502)
            req = self.request(cont, params=params, auth=auth)
            cont = None
            if not req:
                # status code different than 2XX
                raise HandlerError("Cannot find resource on version server. API response %d'd " % req.status_code,
                                   404)
            result = req.json()
            if 'message' in result:
                # API-specific error
                raise HandlerError(result['message'])
            if 'errors' in result:
                # API-specific error
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

        if queries_results:
            # Processes results based on resource type
            return map(mapper, queries_results)
        else:
            # No results found
            raise HandlerError("Resource not found, empty response from API",
                               404)
