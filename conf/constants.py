__author__ = 'Yorick Chollet'

import re
from configparser import ConfigParser

### Code constants
HTTP_STATUS = {
    200: "200 OK",
    405: "405 Method Not Allowed",
    404: "404 Not Found",
    302: "302 Found",
    400: "400 Bad Request",
    413: "Request Entity Too Large",
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

JSONSTR = 'json'
LINKSTR = 'link'

EXTENSIONS_PATH = 'core/extensions/'

LOG_FMT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'

TIME_OUT = 10  # seconds


#TODO add decode('iso-8859-1')
#TODO def max timemap size for security


### Configuration constants

conf = ConfigParser()
conf.read('conf/config.cfg')

## Server configuration
HOST = conf.get('server', 'host')
STRICT_TIME = conf.getboolean('server', 'strict_datetime')

## Handler(s) configuration
SINGLE_HANDLER = conf.getboolean('handler', 'single')
if conf.getboolean('handler', 'is_vcs'):
    RESOURCE_TYPE = 'vcs'
else:
    RESOURCE_TYPE = 'snapshot'

## Cache
# When False, all cache requests will be cache MISSes
CACHE_USE = conf.getboolean('cache', 'activated')
# Cache values expire after one day.
CACHE_EXP = conf.getint('cache', 'expiration_seconds')
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = conf.getint('cache', 'tolerance_seconds')
# Cache files paths
CACHE_FILE = conf.get('cache', 'fdata')
CACHE_RWLOCK = conf.get('cache', 'flock')
CACHE_DLOCK = conf.get('cache', 'fdogpile')

