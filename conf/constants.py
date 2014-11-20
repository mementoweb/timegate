__author__ = 'Yorick Chollet'

from configparser import ConfigParser

### Code constants
HTTP_STATUS = {
    200: "200 OK",
    302: "302 Found",
    400: "400 Bad Request",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    416: '416 Requested Range Not Satisfiable',
    500: "500 Internal Server Error",
    502: "502 Bad Gateway",
    501: "501 Not Implemented",
    503: "503 Service Unavailable"
}

TIMEMAP_URI_PART = 'timemap'
TIMEGATE_URI_PART = 'timegate'

DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'

MIME_TYPE_JSON = 'application/json'
MIME_TYPE_LINK = 'application/link-format'

JSON_URI_PART = 'json'
LINK_URI_PART = 'link'

EXTENSIONS_PATH = 'core/extensions/'

LOG_FORMAT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'

TM_MAX_SIZE = 25000

#TODO add decode('iso-8859-1')


### Configuration constants

conf = ConfigParser()
conf.read('conf/config.cfg')

## Server configuration
HOST = unicode.encode(conf.get('server', 'host'), 'utf-8')
STRICT_TIME = conf.getboolean('server', 'strict_datetime')
API_TIME_OUT = conf.getfloat('server', 'api_time_out')

## Handler(s) configuration
SINGLE_HANDLER = conf.getboolean('handler', 'single')
if conf.getboolean('handler', 'is_vcs'):
    RESOURCE_TYPE = 'vcs'
else:
    RESOURCE_TYPE = 'snapshot'

## Cache
# When False, all cache requests will be cache MISSes
CACHE_ACTIVATED = conf.getboolean('cache', 'activated')
# Cache values expire after one day.
CACHE_EXP = conf.getint('cache', 'expiration_seconds')
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = conf.getint('cache', 'tolerance_seconds')
# Cache files paths
CACHE_FILE = conf.get('cache', 'fdata')
CACHE_RWLOCK = conf.get('cache', 'flock')
CACHE_DLOCK = conf.get('cache', 'fdogpile')

