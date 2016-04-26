..
    This file is part of TimeGate
    Copyright (C) 2016 CERN.

    TimeGate is free software; you can redistribute it and/or modify
    it under the terms of the Revised BSD License; see LICENSE file for
    more details.

Installation
============

In this installation guide, we’ll create a basic TimeGate instance.

.. code-block:: console

   $ pip install -e git+https://github.com/mementoweb/timegate.git#egg=TimeGate
   $ uwsgi --http :9999 -s /tmp/mysock.sock --module timegate.application --callable application
