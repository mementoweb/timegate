__author__ = 'Yorick Chollet'

from dateutil.relativedelta import relativedelta
import tgutils

from handler import validate_response

from dogpile.cache import make_region

from errors.handlererror import HandlerError
from errors.cacheerror import CacheError

import logging


# cache expiration TODO push to constants
TEN_DAYS = 3600 * 24 * 10


class Cache:

    def __init__(self, tolerance=0, enabled=True):
        self.tolerance = relativedelta(seconds=tolerance)
        self.enabled = enabled
        #TODO pass in configure
        self.backend = make_region().configure(
            'dogpile.cache.dbm',
            expiration_time=TEN_DAYS,
            arguments={
                'filename': 'core/cache_data',
                'rw_lockfile': 'core/cache_rwlock',
                'dogpile_lockfile': 'core/cache_dogpilelock'
            }
        )

    def get_until(self, memento, date, getter, *args, **kwargs):
        if not self.enabled:
            return getter(*args, **kwargs)

        # No need to refresh if table young enough
        try:
            val = self.backend.get(memento)
        except Exception as e:
            raise CacheError("Exception loading cache content: %s" % e.message)

        age = 0
        timemap = None

        if val:
            age = val[0]
            timemap = val[1]
            logging.info("Cached value exists for %s" % memento)
        else:
            logging.info("No cached value for %s" % memento)

        if not val or date > age + self.tolerance:
            # Cache possibly outdated
            try:
                (uri, timemap) = validate_response(getter(*args, **kwargs))
            except HandlerError as he:
                raise he
            except Exception as e:
                raise e
                raise HandlerError("Error getting and parsing handler response: %s" % e.message)
            self.set(memento, timemap)

        return timemap

    def get_all(self, memento, getter, *args, **kwargs):
        # No way to know if table is new other than retrieve one.
        # Hope to retrieve in the tolerance delta.
        return self.get_until(memento, tgutils.now(), getter, *args, **kwargs)

    def set(self, memento, timemap):
        logging.info("Updating cache for %s" % memento)
        age = tgutils.now()
        val = (age, timemap)
        key = memento
        return self.backend.set(key, val)