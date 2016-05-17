.. _http_response_headers:

Memento and HTTP
================

The Memento framework requires specific HTTP headers in order to work
properly. They must be added to the server's response headers for any
Original Resources or Mementos request.

Intuitively, a user needs to be able to know which server to contact to
do the time negotiation. Hence a link to the TimeGate is needed from
both the Original Resource and the Mementos. Additionally, a Memento is
defined by an Original Resource it is the snapshot of, and the date time
at which it was created. Thus, it carries a link to its Original
Resource and a datetime information.

Example
-------

Let's take the following example: Suppose a server is handling requests
for the following URIs:

.. image:: uris_example.png

Each time a server responds to requests for any of these URIs, standards
HTTP headers are returned. With Memento, the following headers are
added: - For the Original Resource, add a "Link" header that points at
its TimeGate - For each Memento, add a "Link" header that points at the
TimeGate - For each Memento, add a "Link" header that points to the
Original Resource - For each Memento, add a Memento-Datetime header that
conveys the snapshot datetime

Using the previous example, and supposing a TimeGate server is running
at ``http://example.com/timegate/``, Memento HTTP response headers for
the Original Resource and one Memento look as follows:

.. image:: uris_example.png

To sum up
---------

-  The ``Memento-Datetime:`` header is a Memento-specific header which
   value is the `rfc1123 <http://tools.ietf.org/html/rfc1123>`__-date of
   the Memento.
-  It must be included in any response to a Memento request.
-  It cannot be in an Original Resource response.
-  The ``Link:`` header is a standard header to which new values are
   added.
-  A link to the TimeGate with relation ``rel="timegate"`` must be
   included in all Memento and Original Resource responses.
-  A link to the Original Resource with relation ``rel="original"`` must
   be included in all Memento responses.
-  Link with relation ``rel="original"`` cannot be in an Original
   Resource response.
