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


def test_version():
    """Test version import."""
    from timegate import __version__
    assert __version__


def test_application(client):
    """Test simple request."""
    assert client.get('/').status_code == 400
