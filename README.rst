Memento TimeGate
================

.. image:: https://img.shields.io/travis/mementoweb/timegate.svg
           :target: https://travis-ci.org/mementoweb/timegate

About
-----

Make your web resources `Memento <http://www.mementoweb.org>`__ compliant in a
few easy steps.

The Memento framework enables datetime negotiation for web resources.
Knowing the URI of a Memento-compliant web resource, a user can select a
date and see what it was like around that time.

Installation
------------

Memento TimeGate is on PyPI so all you need is: ::

  pip install -e git+https://github.com/mementoweb/timegate.git#egg=TimeGate
  uwsgi --http :9999 -s /tmp/mysock.sock --module timegate.application --callable application


Documentation
-------------

The documentation is readable at http://timegate.readthedocs.io or can be built
using Sphinx: ::

  pip install timegate[docs]
  python setup.py build_sphinx


Testing
-------

Running the test suite is as simple as: ::

  ./run-tests.sh
