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

import pytest


def test_version():
    """Test version import."""
    from timegate import __version__
    assert __version__


def test_initialization():
    """Test TimeGate initialization."""
    from timegate.application import TimeGate
    from timegate.examples.simple import ExampleHandler
    handler = ExampleHandler()
    app = TimeGate(config=dict(HANDLER_MODULE=handler))
    assert handler == app.handler


def test_application():
    """Test simple request."""
    from timegate import application
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse
    client = Client(application.application, BaseResponse)

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
        headers=[('Accept-Datetime', 'Mon, 01 Jan 1999 00:00:00 GMT'), ],
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v1'
    )

    response = client.get(
        '/timegate/http://www.example.com/resourceA',
        headers=[('Accept-Datetime', 'Mon, 01 Jan 2010 00:00:00 GMT'), ],
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v1'
    )

    response = client.get(
        '/timegate/http://www.example.com/resource%20space'
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/space'
    )


def test_closest_match(app):
    """Test closes match."""
    from werkzeug.test import Client
    from werkzeug.wrappers import BaseResponse

    app.config['RESOURCE_TYPE'] = 'snapshot'
    client = Client(app, BaseResponse)

    response = client.get(
        '/timegate/http://www.example.com/resourceA',
        headers=[('Accept-Datetime', 'Mon, 01 Jan 2010 00:00:00 GMT'), ],
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v2'
    )

    response = client.get(
        '/timegate/http://www.example.com/resourceA',
        headers=[('Accept-Datetime', 'Mon, 01 Jan 2100 00:00:00 GMT'), ],
    )
    assert response.status_code == 302
    assert response.headers['Location'] == (
        'http://www.example.com/resourceA_v3'
    )


@pytest.mark.parametrize('value,result', [
    ('', ''), ('/', '/'), ('#', ''),
])
def test_uri_validation(value, result):
    """Test URI validation."""
    from timegate.utils import validate_uristr
    assert result == validate_uristr(value)


def test_uri_validation_exceptions():
    """Test URI validation exceptions."""
    from timegate.utils import validate_uristr
    with pytest.raises(Exception):
        validate_uristr(None)
