__author__ = 'Yorick Chollet'

# Base URI of the TimeGate program
HOST = 'http://127.0.0.1:9999'

# When True, the user must follow the exact datetime Format.
STRICT_TIME = True

# The timegate will use 'closest' as the function for best Memento
BEST = 'closest_past'

# Cache values expire after one day.
CACHE_EXP = 3600 * 24
# When False, all cache requests will be cache MISSes
CACHE_USE = True
# Time window in which the cache value is considered young enough to be valid
CACHE_TOLERANCE = 3600
# Cache files paths
CACHE_FILE = 'core/cache_data'
CACHE_RWLOCK = 'core/cache_rwlock'
CACHE_DLOCK = 'core/cache_dogpilelock'

SINGLE_HANDLER = True