# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""PY2/PY3 compatibility layer."""

import sys

PY2 = sys.version_info[0] == 2

if not PY2:  # pragma: no cover
    from urllib.parse import urlparse, quote

    text_type = str
    string_types = (str,)
    integer_types = (int,)
else:  # pragma: no cover
    from urlparse import urlparse
    from urllib2 import quote

    text_type = unicode
    string_types = (str, unicode)
    integer_types = (int, long)
