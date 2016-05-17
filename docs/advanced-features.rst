.. _advanced_features:

TimeMaps
========

The TimeGate can easily be used as a TimeMap server too. ## Requirements
For that there are two requirements:

- The Handler must implement the ``get_all_mementos(uri_r)`` function to return
  the entire history of an Original Resource.


- The ``conf/config.ini`` file must have the variable ``use_timemap = true``.

Resulting links
---------------

Once this setup is in place, the TimeGate responses' ``Link`` header
will contain two new relations, for two different formats (MIME types):

- ``<HOST/timemap/link/URI-R>; rel="timemap"; type="application/link-format"``
  `Link TimeMaps <http://www.mementoweb.org/guide/rfc/#Pattern6>`_

- ``<HOST/timemap/json/URI-R>; rel="timemap"; type="application/json"`` JSON
  TimeMaps

Where ``HOST`` is the base URI of the program and ``URI-R`` is the URI
of the Original Resource.

Example
-------

For example, suppose ``http://www.example.com/resourceA`` is the URI-R
of an Original Resource. And suppose the TimeGate/TimeMap server's
``host`` configuration is set to ``http://timegate.example.com`` Then,
HTTP responses from the TimeGate will include the following:

- ``<http://timegate.example.com/timemap/link/http://www.example.com/resourceA>; rel="timemap"; type="application/link-format"``
- ``<http://timegate.example.com/timemap/json/http://www.example.com/resourceA>; rel="timemap"; type="application/json"``

Now a user can request an ``HTTP GET`` on one of those link and the
server's response will have a ``200 OK`` status code and its body will
be the TimeMap.

HandlerErrors
=============

Custom error messages can be sent to the client using the custom
exception module: ``from errors.timegateerrors import HandlerError``.
For instance, a custom message with HTTP status ``400`` and body
``Custom error message`` can be sent using:
``raise HandlerError("Custom error message", status=400)``. Raising a
``HandlerError`` will stop the request and not return any Memento to the
client.
