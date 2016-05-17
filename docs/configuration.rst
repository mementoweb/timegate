.. _configuration:

Configuring the server
======================

Edit the `config
file <https://github.com/mementoweb/timegate/blob/master/conf/config.ini>`__:
``conf/config.ini``.

Mandatory field
---------------

``host`` Is the server's base URI. This is the URI on which the TimeGate
is deployed. No default value.

Example: - Suppose TimeGate is running at ``http://tg.example.com`` and
``URI-R`` refers to an Orignal Resource's URI.

- The program will respond to TimeGate requests at
  ``http://tg.example.com/timegate/URI-R``

- The program will respond to ``TimeMap`` requests at
  ``http://tg.example.com/timemap/link/URI-R`` and
  ``http://tg.example.com/timemap/json/URI-R`` if the feature is enabled.
  See :ref:`advanced_features`.

Important field
---------------

``is_vcs`` The type of archive affects the best Memento selection
algorithm. Default ``false``. - When ``false``, the history is
considered to be snapshots taken at some points in time, thus the best
memento is the *absolute* closest to the requested date. - When
``true``, the history the handler returns is considered to be from a
version control system. In other words, the history represents every
change that was made to the Original Resource and the exact datetimes of
the change. In this case, the best Memento for a requested datetime T
will be the closest *before* T.

Other fields
------------

-  ``handler_class`` (Optional) Python module path to a handler class.
   This is useful if the handler is composed of several classes or to
   quickly switch between handlers. If this parameter is not provided,
   the program will search for handler classes in ``core.handler``. For
   example:
   ``handler_class = core.handler_examples.wikipedia.WikipediaHandler``
-  ``api_time_out`` Time, in seconds, before a request to an API times
   out when using the ``Handler.request()`` function. Default 6 seconds
-  ``base_uri`` (Optional) String that will be prepended to requested
   URI if missing. This can be used to shorten the request URI and to
   avoid repeating the base URI that is common to all resources. Default
   empty
-  For example, suppose the TimeGate is deployed at
   ``http://tg.example.com``
-  Suppose every Original Resources ``URI-Ri`` has the following format
   ``http://resource.example.com/res/URI-Ri``
-  Then, Setting ``base_uri = http://resource.example.com/res/`` will
   allow short requests such as for example
   ``http://tg.example.com/timegate/URI-Ri`` instead of
   ``http://tg.example.com/timegate/http://resource.example.com/res/URI-Ri``.
-  ``use_timemap`` When ``true``, the TimeGate adds TimeMaps links to
   its (non error) responses. Default ``false``

Cache parameters:
-----------------

-  ``cache_activated`` When ``true``, the cache stores the entire
   history of an Original Resource from handlers that allows batch
   ``get_all_mementos(uri_r)`` requests. It can then respond from cache
   if the value is fresh enough. If a requests contains the header
   ``Cache-Control: no-cache`` the server will not respond from cache.
   When ``false`` the cache files are not created. Default ``true``.
-  ``cache_refresh_time`` tolerance in seconds, for which it is assumed
   that a history didn't change. Any TimeGate request for a datetime
   past this (or any TimeMap request past this) will trigger a refresh
   of the cached history. Default 86400 seconds (one day).
-  ``cache_directory`` Relative path for data files. Do not add any
   other file to this directory as they could be deleted. Each file
   represents an entire history of an Original Resource. Default
   ``cache/``.
-  ``cache_max_values`` Maximum number of URI-Rs for which its entire
   history is stored. This is then the number of files in the
   ``cache_directory``. Default 250.

See :ref:`cache`.
