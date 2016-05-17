Memento Framework
=================

Resources on the web change over time. While many server keep archives
of what these resources looked like in the past, it is often difficult
for the user to retrieve the URI of such an archive for a specific point
in time.

The `Memento Framework <http://www.mementoweb.org/>`__ leverages the
need for the user to do the search by hand.

Components
----------

-  Suppose a web resource is located at some URI. We call the resource
   the **Original Resource** and refer to its URI as the **URI-R**. This
   is the resource for which a user wants to find a prior version.
-  A prior version of an Original Resource is called a **Memento** and
   we refer to its URI as the **URI-M**. There could be many Mementos
   for one Original Resource. Each having its own URI-Mi and each
   encapsulating the state of the Original Resource at a specific point
   in time.
-  The **TimeGate** is the application which selects the best Memento of
   an Original Resource for a given datetime. This is where datetime
   negotiation happens.

Requirements
------------

-  The first requirements is that Original Resources and Mementos must
   be accessible through their respective and unique URIs.
- Also, the framework operates using HTTP headers to work. Headers of requests
   from/to the TimeGate are taken care of. However, Original Resources and
   Mementos require the add of new headers. (See :ref:`http_response_headers`.)

The Generic TimeGate
--------------------

The TimeGate is where most of the Memento magic happens. And its
implementation is likely to be extremely close from one server to
another. In this sense, its processing of HTTP requests / responses
headers, its algorithms and logic can be abstracted and made generic.
The only thing server-specific is the management of URIs and datetimes.
To do that, this TimeGate can fit any web resource if it is provided a
way to retrieve a history of a specific Original Resource. This is made
using a custom handler.  (See :ref:`handler`.)

More about Memento
------------------

-  Details about Memento are available in the `RFC
   7089 <http://www.mementoweb.org/guide/rfc/>`__.
-  A `quick intro <http://www.mementoweb.org/guide/quick-intro/>`__ is
   available on Memento's website.
