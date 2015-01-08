import re
import requests

__author__ = 'Yorick Chollet'

from core.handler_baseclass import Handler
from errors.timegateerrors import HandlerError

import time

ACCEPTABLE_RESOURCE = """Acceptable resources URI: repositories (github.com/:user/:repo), folders (github.com/:user/:repo/tree/:branch/:path), files (github.com/:user/:repo/blob/:branch/:path) and raw files (raw.githubusercontent.com/:user/:repo/:branch/:path)"""


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
                              (/.*)?  # optional path
                              """, re.X)  # verbosed: ignore whitespaces and \n
        self.header_rex = re.compile('<(.+?)>; rel="next"')  # The regex for the query continuation header
        self.file_rex = re.compile('(/blob)?/master')  # The regex for files

    def get_all_mementos(self, uri):
        MAX_TIME = 120 #seconds

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

        path = ''
        branch = ''
        # Processes one result to (memento, datetime) pair
        mapper = None

        # Defining Resource type and response handling
        # Creates one function for a specific type to map the results to memento pairs.
        if base == 'github.com/':
            # Resource is a repository
            if not req_path or req_path == '/':
                if req_path:
                    path = '/'

                def make_pair(commit):
                    return (commit['html_url'].replace('commit', 'tree'),
                            commit['commit']['committer']['date'])
                mapper = make_pair

            # Resource is a file
            elif req_path.startswith('/blob/'):
                path = req_path.replace('/blob/', '', 1)
                branch_index = path.find('/')
                branch = path[:branch_index]
                path = path[branch_index:]
                if branch == '' or path == '' or path.endswith('/'):
                    raise HandlerError("Not found. Empty path for file in repository", 404)

                def make_pair(commit):
                    # HTML Resource
                    memento_path = '/blob/%s%s' % (commit['sha'], path)
                    uri_m = '%s%s%s/%s%s' % (
                        protocol, base, user, repo, memento_path)
                    return (uri_m, commit['commit']['committer']['date'])
                mapper = make_pair

            # Resource is a directory
            elif req_path.startswith('/tree/'):
                path = req_path.replace('/tree/', '', 1)
                branch_index = path.find('/')
                if branch_index < 0:
                    branch_index = len(path)
                branch = path[:branch_index]
                path = path[branch_index:]
                if branch == '':
                    raise HandlerError("Not found. Empty branch path", 404)

                def make_pair(commit):
                    return (commit['html_url'].replace('commit', 'tree')+path,
                            commit['commit']['committer']['date'])
                mapper = make_pair

        # Resource is a raw file
        elif base == 'raw.githubusercontent.com/' and req_path is not None:
            path = req_path.replace('/', '', 1)
            branch_index = path.find('/')
            branch = path[:branch_index]
            path = path[branch_index:]
            is_online = bool(requests.head(uri))  # must be done because API does not make any difference between path or files
            if path == '' or path.endswith('/') or not is_online:
                raise HandlerError("'%s' not found: Raw resource must be a file." %path, 404)

            def make_pair(commit):
                memento_path = '/%s%s' % (commit['sha'], path)
                uri_m = '%s%s%s/%s%s' % (protocol, base, user, repo, memento_path)
                return (uri_m, commit['commit']['committer']['date'])
            mapper = make_pair

        if mapper is None:
            # The resource is not accepcted.
            raise HandlerError("GitHub resource type not found." + ACCEPTABLE_RESOURCE, 404)

        # Initiating request variables
        apibase = '%s/repos/%s/%s/commits' % (self.api, user, repo)
        params = {
            'per_page': 100,  # Max allowed is 100
            'path': str(path),
            'sha': str(branch)
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
                raise HandlerError("Cannot find resource on version server. API response %d'd " % req.status_code, 404)
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
            raise HandlerError("Resource not found, empty response from API", 404)
