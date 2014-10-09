__author__ = 'Yorick Chollet'

import re

#TODO move to constants

HTTP_STATUS = {
    200: "200 OK",
    404: "404 Not Found",
    302: "302 Found",
    400: "400 Bad Request",
    503: "503 Service Unavailable"
}

URI_PARTS = {
    'G': 'timegate',
    'T': 'timemap'
}

#TODO remove
PROXIES = {'http': 'http://blueone.lanl.gov:8080',
           'https': 'http://blueone.lanl.gov:8080'}

DATEFMT = '%a, %d %b %Y %H:%M:%S GMT'

HTTPRE = re.compile('https?://', re.IGNORECASE)
WWWRE = re.compile('www.', re.IGNORECASE)