__author__ = 'Yorick Chollet'

from dateutil.relativedelta import relativedelta
import logging
from dogpile.cache import make_region

from conf.config import CACHE_EXP, CACHE_FILE, CACHE_RWLOCK, CACHE_DLOCK, CACHE_TOLERANCE
from errors.handlererror import HandlerError
from errors.cacheerror import CacheError
from handler import validate_response
import tgutils


class Cache:

    def __init__(self, tolerance=CACHE_TOLERANCE, file=CACHE_FILE, expiration=CACHE_EXP, enabled=True):
        """
        Constructor method
        :param tolerance: The tolerance, in seconds to which a TimeMap is considered young enough to be used as is.
        :param file: The path of the cache database file.
        :param expiration: How long, in seconds, the cache entries are stored
        :param enabled: To quickly enable/disable the cache. If not enabled,
        every get will be a CACHE MISS.
        :return:
        """
        self.tolerance = relativedelta(seconds=tolerance)
        self.enabled = enabled
        self.backend = make_region().configure(
            'dogpile.cache.dbm',
            expiration_time=expiration,
            arguments={
                'filename': file,
                'rw_lockfile': CACHE_RWLOCK,
                'dogpile_lockfile': CACHE_DLOCK
            }
        )
        logging.info("Cached started: cache file: %s, cache expiration: %d seconds, cache tolerance: %d seconds" % (CACHE_FILE, CACHE_EXP, CACHE_TOLERANCE))

    def get_until(self, uri_r, date):
        """ # TODO recomment
        Returns the timemap (memento,datetime)-list for the requested memento.
        The timemap is garanteed to span at least until the 'date' parameter,
        within the tolerance.
        :param uri_r: The URI-R of the resource as a string
        :param date: The target date. It is the accept-datetime for timegate
        requests, and the current date. The cache will return all mementos
        prior to this date (within cache.tolerance parameter)
        :param getter: The function to use in case of a cache miss
        :param args: getter function arguments
        :param kwargs: getter function named arguments
        :return: (memento_uri_string, datetime_obj)-list
        """

        # Cache MISS if not enabled
        if not self.enabled:
            return None

        # Query the backend for stored cache values to that memento
        try:
            val = self.backend.get(uri_r)
        except Exception as e:
            raise CacheError("Exception loading cache content: %s" % e.message)

        if val:
            # There is a value in the cache
            timetamp = val[0]
            timemap = val[1]
            logging.info("Cached value exists for %s" % uri_r)
            if date > timetamp + self.tolerance:
                logging.info("Cache MISS: value outdated for %s" % uri_r)
                timemap = None
            else:
                logging.info("Cache HIT: found value for %s" % uri_r)
        else:
            # Cache MISS: No value
            logging.info("Cache MISS: No cached value for %s" % uri_r)
            timemap = None

        return timemap

    def get_all(self, uri_r):
        """
        Request the whole timemap for that uri
        :param uri_r: the URI-R of the resource
        :param getter: The function to use in case of a cache miss
        :param args: getter function arguments
        :param kwargs: getter function named arguments
        :return: (memento_uri_string, datetime_obj)-list
        """
        # No way to know if table is new other than retrieve one.
        # Hope to retrieve in the tolerance delta.
        return self.get_until(uri_r, tgutils.now())

    def refresh(self, uri_r, getter, *args, **kwargs):
        try:
            # Requests the data
            (uri, timemap) = validate_response(getter(*args, **kwargs))
        except HandlerError as he:
            raise he
        except Exception as e:
            raise HandlerError("Error getting and parsing handler response: %s" % e.message)
        if self.enabled:
            # Creates or refreshes the new timemap for that URI-R
            self.set(uri_r, timemap)
        return timemap

    def set(self, uri_r, timemap):
        """
        Sets / refreshes the cached timemap for that URI-R. And appends it with
        a timestamp.
        :param uri_r: The URI-R of the original resource
        :param timemap:
        :return: the backend setter method return value.
        """
        logging.info("Updating cache for %s" % uri_r)
        timestamp = tgutils.now()
        val = (timestamp, timemap)
        key = uri_r
        return self.backend.set(key, val)