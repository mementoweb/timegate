__author__ = 'Yorick Chollet'

import re

#TODO split constants and config

HTTP_STATUS = {
    200: "200 OK",
    405: "405 Method Not Allowed",
    404: "404 Not Found",
    302: "302 Found",
    400: "400 Bad Request",
    503: "503 Service Unavailable"
}

TIMEMAPSTR = 'timemap'
TIMEGATESTR = 'timegate'

#TODO remove
PROXIES = {'http': 'http://blueone.lanl.gov:8080',
           'https': 'http://blueone.lanl.gov:8080'}

DATEFMT = '%a, %d %b %Y %H:%M:%S GMT'

HTTPRE = re.compile('https?://', re.IGNORECASE)
WWWRE = re.compile('www.', re.IGNORECASE)

HOST = 'http://127.0.0.1:9000'

EXTENSIONS_PATH = 'core/extensions/'

LOG_FMT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'

STRICT_TIME = True  # If the time MUST follow DATEFMT

BEST = 'closest'

USE_CACHE = True  # dogpile

#TODO add decode('iso-8859-1')
#TODO add timegate/timemap strings
#TODO def max timemap size for security