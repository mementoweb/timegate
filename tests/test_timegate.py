# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import json


def test_version():
    """Test version import."""
    from timegate import __version__
    assert __version__


def test_application(client):
    """Test simple request."""
    assert client.get('/').status_code == 404


def test_timemap_response(client):
    """Test timemap responses."""
    response = client.get(
        '/timemap/json/http://www.example.com/resourceBad'
    )
    assert response.status_code == 404

    response = client.get(
        '/timemap/json/http://www.example.com/resourceA'
    )
    assert response.status_code == 200

    response = client.get(
        '/timemap/json/resourceA'
    )
    assert response.status_code == 200
    data = json.loads(response.data.decode('utf-8'))
    assert 3 == len(data['mementos']['list'])

    response = client.get(
        '/timemap/link/http://www.example.com/resourceA'
    )
    assert response.status_code == 200
    mementos = response.data.split(b'\n')
    assert 8 == len(mementos)


def test_timegate_response(client):
    """Test timegate responses."""
    response = client.get(
        '/timegate/http://www.example.com/resourceA'
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v3'
    )

    response = client.get(
        '/timegate/http://www.example.com/resourceA',
        headers=[('Accept-Datetime', 'Mon, 01 Jan 2000 00:00:00 GMT'), ],
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v1'
    )
