__author__ = 'Yorick Chollet'

HOST = 'http://127.0.0.1:9999'
STRICT_TIME = True  # If the time MUST follow DATEFMT

BEST = 'closest'

CACHE_EXP = 3600 * 24  # one day
CACHE_USE = True  # dogpile
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = 3600
CACHE_FILE = 'core/cache_data'
CACHE_RWLOCK = 'core/cache_rwlock'
CACHE_DLOCK = 'core/cache_dogpilelock'