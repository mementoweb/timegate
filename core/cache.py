import hashlib, os
from core import timegate_utils
__author__ = 'Yorick Chollet'

from dateutil.relativedelta import relativedelta
import logging

from errors.timegateerrors import HandlerError, CacheError
from handler import validate_response

from werkzeug.contrib.cache import FileSystemCache


class Cache:

    def __init__(self, path, tolerance, expiration, max_size):
        """
        Constructor method
        :param tolerance: The tolerance, in seconds to which a TimeMap is considered young enough to be used as is.
        :param path: The path of the cache database file.
        :param expiration: How long, in seconds, the cache entries are stored
        every get will be a CACHE MISS.
        :return:
        """

        # TODO add LRU somewhere environ 100MB
        self.tolerance = relativedelta(seconds=tolerance)
        self.path = path.rstrip('/')  # +'.db'
        self.max_file_size = 1e+6  # TODO from len(uri) * tmsize + x
        self.max_values = int(max_size / self.max_file_size)

        self.backend = FileSystemCache(path,
                                       threshold=3,  # self.max_values
                                       default_timeout=expiration)  # TODO configurations
        logging.debug("Cache created. max_files = %d. Expiration = %d " % (self.max_values, expiration))

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
        # Query the backend for stored cache values to that memento
        key = uri_r
        try:
            val = self.backend.get(key)
        except Exception as e:
            logging.error("Exception loading cache content: %s" % e.message)
            raise CacheError("Exception loading cache content")

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
        return self.get_until(uri_r, timegate_utils.now())

    def refresh(self, uri_r, getter, *args, **kwargs):
        try:
            # Requests the data
            timemap = validate_response(getter(*args, **kwargs))
        except HandlerError as he:
            raise he
        except Exception as e:
            logging.error("Error getting and parsing handler response: %s" % e.message)
            raise HandlerError("Error getting and parsing handler response")
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
        timestamp = timegate_utils.now()
        val = (timestamp, timemap)
        key = uri_r
        try:
            self.backend.set(key, val)
            self.check_size(uri_r)
        except Exception as e:
            logging.error("Error setting cache value: %s" % e.message)
            raise CacheError("Error setting cache value")

    def check_size(self, uri, delete=True):
        try:
            fpath = self.path+'/' + md5(uri)
            size = os.path.getsize(fpath)
            if size > self.max_file_size and delete:
                logging.warning("Cache value too big (%dB, max %dB) and deleted: TimeMap of %s" % (size, self.max_file_size, uri))
                os.remove(fpath)
                size = 0
            return size
        except Exception as e:
            logging.error("Exception checking cache value size for %s Exception: %s" % (uri, e.message))
            return 0


# todo cache this
def md5(uri):
    """
    returns the hexadecimal md5 of uri
    """
    m = hashlib.md5()
    m.update(uri)
    return m.hexdigest()