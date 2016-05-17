Getting Started
===============

Memento TimeGate
----------------

TimeGate is a `WSGI <http://wsgi.readthedocs.org/en/latest/>`__
application server that allows simple implementation of
`Memento <http://mementoweb.org>`__ capabilities for web resources
having accessible revisions. It manages all the content negotiation
logic, from request processing, best memento query and selection to HTTP
response.

To make web resources that is accessible on a web server fully Memento
compliant, two things need to be done. - TimeGate is generic: a custom
handler must be plugged in to match the specific web server. - The
Memento framework uses specific HTTP headers: they must be added to the
resource's web server responses.

Steps
-----

The big picture
~~~~~~~~~~~~~~~

The first thing to do is to understand how the program is
structured.  See :ref:`big_picture`.

Installing the server
~~~~~~~~~~~~~~~~~~~~~

The code can be obtained
`here <https://github.com/mementoweb/timegate/releases>`__. Download a
zip or tar.gz archive into a directory of your choice.

Decompress the zip files using:

.. code:: bash

    $ unzip timegate-<version>.zip

Decompress tar.gz files using:

.. code:: bash

    $ tar xvzf timegate-<version>.tar.gz

Install the dependencies using:

.. code:: bash

    $ echo 'uWSGI>=2.0.3 ConfigParser>=3.3.0r2 python-dateutil>=2.1 requests>=2.2.1 werkzeug>=0.9.6 lxml>=3.4.1' | xargs pip install

Running the TimeGate
~~~~~~~~~~~~~~~~~~~~

Then try starting the TimeGate server with one of the handler that is
already provided. To run it, first navigate to the directory:

.. code:: bash

    $ cd timegate-<version>

Then, there are two possibilities: - Either execute
``uwsgi --http :9999 --wsgi-file core/application.py --master`` to
deploy the TimeGate on ``localhost:9999``. Add the option
``--pidfile /path/to/file.pid`` to store the process ID in a file. - Or
edit the uWSGI launch configuration in ``conf/timegate.ini`` and then
execute ``uwsgi conf/timegate.ini``

To stop the server: - Simply use ``CTRL+C`` if it is running in
foreground. - Or execute ``uwsgi --stop /path/to/file.pid`` if you have
stored the PID to run it in the background. - If by mistake the PID is
not stored but the TimeGate is still running, list all uwsgi processes
using ``ps ux | grep uwsgi``, identify the TimeGate process from the
``COMMAND`` column and kill it using ``kill -INT  <PID>``.

Handler
~~~~~~~

Once the server is successfully running with an example handler that was
provided, edit it or create a new one (see :ref:`handler`) that returns the list
of all URI-Ms given a URI-R of an Original Resource you wish to make Memento
compliant.

Memento Headers
~~~~~~~~~~~~~~~

The Memento protocol mainly works with HTTP headers. Now add the required
headers (see :ref:`http_response_headers`) to your web server's HTTP responses.

Configuring the TimeGate
~~~~~~~~~~~~~~~~~~~~~~~~

Finally, enter the TimeGate's ``HOST`` location in the ``config.ini`` (see
:ref:`configuration`) file. Also edit the other parameters' default values to
your preferences.

Memento compliance
~~~~~~~~~~~~~~~~~~

That's it. The basic Memento functionalities are here and your web
server is now Memento compliant. See :ref:`advanced_features`.
