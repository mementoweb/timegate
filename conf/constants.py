__author__ = 'Yorick Chollet'

import re


#TODO define __all__ for all modules


HTTP_STATUS = {
    200: "200 OK",
    405: "405 Method Not Allowed",
    404: "404 Not Found",
    302: "302 Found",
    400: "400 Bad Request",
    500: "Internal Server Error",
    503: "503 Service Unavailable"
}

TIMEMAPSTR = 'timemap'
TIMEGATESTR = 'timegate'

DATEFMT = '%a, %d %b %Y %H:%M:%S GMT'

HTTPRE = re.compile('https?://', re.IGNORECASE)
WWWRE = re.compile('www.', re.IGNORECASE)

MIME_JSON = 'application/json'

MIME_LINK = 'application/link-format'


EXTENSIONS_PATH = 'core/extensions/'

LOG_FMT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'



#TODO add decode('iso-8859-1')
#TODO def max timemap size for security