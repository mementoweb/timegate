from core import tgutils
import os, sys
import hashlib
from operator import itemgetter


__author__ = 'Yorick Chollet'

from dateutil.relativedelta import relativedelta
import logging
from dogpile.cache import make_region

from errors.timegateerrors import HandlerError, CacheError
from handler import validate_response

from werkzeug.contrib.cache import FileSystemCache


class Cache:

    def __init__(self, path, tolerance, max_size, expiration, rwlock, dlock):
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
        self.path = path.rstrip('/') # +'.db'
        self.max_size = max_size # in Bytes
        # self.backend = make_region().configure(
        #     'dogpile.cache.dbm',
        #     expiration_time=expiration,
        #     arguments={
        #         'filename': data_file,
        #         'rw_lockfile': rwlock,
        #         'dogpile_lockfile': dlock
        #     }
        # )

        self.backend = FileSystemCache(path,
                                       threshold=500,
                                       default_timeout=expiration)  # TODO configurations
        usages, counts = self.backend.get_many('usages', 'counts')
        if not usages:
            usages = {}
        if not counts:
            counts = {}
        self.backend.set('usages', usages)
        self.backend.set('counts', counts)
        # logging.debug("Cache created. Size: %d. usages: %s. couts: %s" % (self.getsize(), usages, counts))

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
        # mutex = self.backend.backend.get_mutex(key)
        try:
            # mutex.acquire()
            # self.increment_count(key)
            val = self.backend.get(key)
        except Exception as e:
            logging.error("Exception loading cache content: %s" % e.message)
            raise CacheError("Exception loading cache content")
        finally:
            pass
            # mutex.release()

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
        timestamp = tgutils.now()
        val = (timestamp, timemap)
        key = uri_r
        # mutex = self.backend.backend.get_mutex(key)
        try:
            # mutex.acquire()
            # self.increment_count(key)
            # size_before = self.getsize(uri_r)
            ret = self.backend.set(key, val)
            # size_after = self.getsize(uri_r)
            # print "Size at backend.set() BF: %d, AF:%d " % (size_before, size_after)
            # self.increment_usage(key, sys.getsizeof(val))
            # if size_after > self.max_size:
            #     self.cleanup(20)  # TODO push to const
        except Exception as e:
            logging.error("Error setting cache value: %s" % e.message)
            raise CacheError("Error setting cache value")
        finally:
            pass
            # mutex.release()

#     def getsize(self, uri=''):
#         if uri:
#             fpath = '/'+md5(uri)
#         else:
#             raise NotImplementedError  # TODO here
#         try:
#             return os.path.getsize(self.path+fpath)
#         except Exception as e:
#             return 0
#
#     def cleanup(self, percents):
#         before_size = self.getsize()
#         to_clean = (percents/100.0) * before_size
#         cleaned = 0
#         keys_to_remove = []
#         counts = self.backend.get('counts')
#         usages = self.backend.get('usages')
#         keys_sorted_by_count = [key for (key, cnt) in sorted(counts.items(), key=itemgetter(1))]
#
#         print keys_sorted_by_count
#
#         for key in keys_sorted_by_count:
#             keys_to_remove.append(key)
#             if key in usages:
#                 size = usages[key]
#                 cleaned += size
#                 del usages[key]
#             else:
#                 cleaned = 0
#             del counts[key]
#             if cleaned > to_clean:
#                 break
#         self.backend.delete_many(keys_to_remove)
#         self.backend.set('usages', usages)
#         self.backend.set('counts', counts)
#         after_size = self.getsize()
#         logging.debug("cleanup(%d)=%d  Old size: %d. New Size: %d. Supposed to have cleaned %d, effective: %d" % (percents, to_clean, before_size, after_size, cleaned, before_size - after_size))
#         logging.info("Cache cleaned up %d Bytes from %d URIs" % (cleaned, len(keys_to_remove)))
#
#     def increment_count(self, key):
#         counts = self.backend.get('counts')
#         if key not in counts:
#             counts[key] = 1
#         else:
#             counts[key] += 1
#         self.backend.set('counts', counts)
#
#     def increment_usage(self, key, size_diff):
#         usages = self.backend.get('usages')
#         if key not in usages:
#             usages[key] = size_diff
#         else:
#             usages[key] += size_diff
#         self.backend.set('usages', usages)
#
#
# # todo cache this
# def md5(uri):
#     """
#     returns the hexadecimal md5 of uri
#     """
#     m = hashlib.md5()
#     m.update(uri)
#     return m.hexdigest()
#
