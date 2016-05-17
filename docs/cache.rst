.. _cache:

Cache
=====

The TimeGate comes with a built-in cache that is activated by default. Change
this behavior editing in the configuration file. See :ref:`configuration`.

Populating the cache
--------------------

The cache stores TimeMaps which is the return values of the handler
function ``get_all_mementos()`` only: - If the Handler does not have
``get_all_mementos()`` implemented, the cache will never be filled. - If
the Handler has both the functions ``get_all_mementos()`` and
``get_memento()``, only TimeMap requests will fill the cache. All
TimeGate requests will use ``get_memento()`` which result will not be
cached.

Cache HIT conditions
--------------------

-  Cached TimeMaps can be used used to respond to a TimeMap request from
   a client if it is fresh enough. The tolerance for freshness can be
   defined in the configuration file.
-  Cached TimeMap can also be used to respond to a TimeGate requests
   from a client. In this case, it is not the request's time that must
   lie within the tolerance bounds, but the requested datetime.

Force Fresh value
-----------------

If the request contains the header ``Cache Control: no-cache``, then the
TimeGate will not return anything from cache.

Example
-------

Suppose you have a TimeMap that was cached at time ``T``. Suppose you
have a tolerance of ``d`` seconds. A TimeMap request arrives at time
``R1``. A TimeGate request arrives at time ``R2`` with requested
datetime j. This request does **not** contain the header
``Cache Control: no-cache``. - A TimeMap request will be served from
cache only if it arrives within the tolerance: ``R1 <= T+d``. - A
TimeGate request will be served from cache only if the requested
datetime happens within the tolerance: ``j <= T+d``, no matter ``R2``.
This means that even if a cached value is old, the cache can still
respond to TimeGate requests for requested datetimes that are until time
``T+d``. - All other requests will be cache misses.

Cache size
----------

There is no "maximum size" parameter. The reason for this is that the
cache size will depend on the average size of TimeMaps, which itself
depends on the length of each URI-Ms it contains, and their average
count. These variables will depend on your system. The cache can be
managed using the ``cache_max_values`` parameter which will affect
indirectly its size.
