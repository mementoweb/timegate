import os
from core import timegate_utils
__author__ = 'Yorick Chollet'

from dateutil.relativedelta import relativedelta
import logging

from errors.timegateerrors import HandlerError, CacheError
from handler import validate_response

from werkzeug.contrib.cache import FileSystemCache, md5


class Cache:

    def __init__(self, path, tolerance, expiration, max_size):
        """
        Constructor method
        :param path: The path of the cache database file.
        :param tolerance: The tolerance, in seconds to which a TimeMap is considered young enough to be used as is.
        :param expiration: How long, in seconds, the cache entries are stored every get will be a CACHE MISS.
        :param max_size: The maximum size, in Bytes for the cache data folder
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
        """
        Returns the TimeMap (memento,datetime)-list for the requested Memento.
        The TimeMap is guaranteed to span at least until the 'date' parameter,
        within the tolerance.
        :param uri_r: The URI-R of the resource as a string
        :param date: The target date. It is the accept-datetime for TimeGate
        requests, and the current date. The cache will return all Mementos
        prior to this date (within cache.tolerance parameter)
        :return: [(memento_uri_string, datetime_obj),...] list if it is in cache and if it is within the cache tolerance for *date*, None otherwise
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
            timestamp, timemap = val
            logging.info("Cached value exists for %s" % uri_r)
            if date > timestamp + self.tolerance:
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
        Request the whole TimeMap for that uri
        :param uri_r: the URI-R of the resource
        :return: [(memento_uri_string, datetime_obj),...] list if it is in cache and if it is within the cache tolerance, None otherwise
        """
        return self.get_until(uri_r, timegate_utils.now())

    def refresh(self, uri_r, getter, *args, **kwargs):
        """
        Refreshes the cached TimeMap for a specific resource and returns it
        :param uri_r: The original resource URI to refresh the TimeMap
        :param getter: The function to call to get a fresh TimeMap
        :param args: *getter* arguments
        :param kwargs: *getter* keywords arguments
        :return: The fresh TimeMap
        """
        try:
            # Requests the data
            timemap = validate_response(getter(*args, **kwargs))
        except HandlerError as he:
            raise he
        except Exception as e:
            logging.error("Error getting and parsing handler response: %s" % e.message)
            raise HandlerError("Error getting and parsing handler response")
        # Creates or refreshes the new timemap for that URI-R
        self._set(uri_r, timemap)
        return timemap

    def _set(self, uri_r, timemap):
        """
        Sets / refreshes the cached TimeMap for that URI-R. And appends it with
        a timestamp of when it is stored.
        :param uri_r: The URI-R of the original resource
        :param timemap: The value to cache
        :return: the backend setter method return value.
        """
        logging.info("Updating cache for %s" % uri_r)
        timestamp = timegate_utils.now()
        val = (timestamp, timemap)
        key = uri_r
        try:
            self.backend.set(key, val)
            self._check_size(uri_r)
        except Exception as e:
            logging.error("Error setting cache value: %s" % e.message)
            raise CacheError("Error setting cache value")

    def _check_size(self, uri, delete=True):
        """
        Checks the size that a specific TimeMap value is using on disk. Deletes if it is more than the maximum size
        :param uri: The TimeMap original resource
        :param delete: (Optional) When true, the value is deleted. Else only a warning is raised.
        :return: the size of the value on disk (0 if it was deleted)
        """
        try:
            fname = md5(uri).hexdigest()  # werkzeug key
            fpath = self.path+'/' + fname
            size = os.path.getsize(fpath)
            if size > self.max_file_size and delete:
                message = "Cache value too big (%dB, max %dB) for the TimeMap of %s"
                if delete:
                    message += ". Deleting cached value."
                    os.remove(fpath)
                    size = 0
                logging.warning(message % (size, self.max_file_size, uri))
            return size
        except Exception as e:
            logging.error("Exception checking cache value size for TimeMap of %s Exception: %s" % (uri, e.message))
            return 0

