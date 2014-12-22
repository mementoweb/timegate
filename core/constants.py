__author__ = 'Yorick Chollet'

from configparser import ConfigParser
# TODO add all in one dictionnary
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

EXTENSIONS_PATH = 'core/extension/'

LOG_FORMAT = '%(asctime)s | %(levelname)s| %(message)s'
LOG_FILE = 'log.txt'

TM_MAX_SIZE = 100000


### Configuration constants

conf = ConfigParser()
conf.read('conf/config.ini')

## Server configuration
HOST = unicode.encode(conf.get('server', 'host'), 'utf-8').rstrip('/')
STRICT_TIME = conf.getboolean('server', 'strict_datetime')
API_TIME_OUT = conf.getfloat('server', 'api_time_out')

## Handler configuration
MOD_PATH = None
BASE_URI = ''
if conf.has_option('handler', 'handler_class'):
    MOD_PATH = unicode.encode(conf.get('handler', 'handler_class'), 'utf-8')
if conf.has_option('handler', 'base_uri'):
    BASE_URI = unicode.encode(conf.get('handler', 'base_uri'), 'utf-8')
if conf.getboolean('handler', 'is_vcs'):
    RESOURCE_TYPE = 'vcs'
else:
    RESOURCE_TYPE = 'snapshot'

## Cache
# When False, all cache requests will be cache MISS
CACHE_USE = conf.getboolean('cache', 'activated')
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = conf.getint('cache', 'refresh_time')
# Cache files paths
CACHE_DIRECTORY = unicode.encode(conf.get('cache', 'cache_directory'), 'utf-8').rstrip('/')
# Cache data file maximum size (in bytes)
CACHE_MAX_SIZE = long(conf.getfloat('cache', 'cache_max_size') * 1e+6)
# Cache files paths
CACHE_FILE = CACHE_DIRECTORY #+ '/cache_data'
# Cache expiration (space bound) in seconds
CACHE_EXP = 259200  # Three days
