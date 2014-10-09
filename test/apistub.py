from urlparse import urlparse

from dateutil import parser


__author__ = 'Yorick Chollet'

debug = False


def application(env, start_response):
    """
    WSGI application object. Emulating the Example API.
    """

    req = env.get("PATH_INFO")
    # Standard Response
    status = '200 OK'
    headers = [('Content-Type', 'application/json; charset=utf-8')]

    if req.startswith('/single'):
        body = [
            """
            {
                "original_uri": "http://foo.bar/",
                "timegate_uri": "http://an.archive.org/timegate/http://foo.bar/",
                "timemap_uri": {
                    "json_format": "http://an.archive.org/timemap/json/http://foo.bar/",
                    "link_format": "http://an.archive.org/timemap/link/http://foo.bar/"
                },
                "mementos": {
                    "first": {
                        "datetime": "2000-06-21T04:41:56Z",
                        "uri": "http://an.archive.org/20000621044156/http://www.foo.bar/"
                    },
                    "last": {
                        "datetime": "2012-08-31T12:22:34Z",
                        "uri": "http://an.archive.org/20120831122234/http://foo.bar/"
                    },
                    "all": [
                        {
                            "datetime": "2000-06-21T04:41:56Z",
                            "uri": "http://an.archive.org/20000621044156/http://foo.bar/"
                        },
                        {
                            "datetime": "2008-04-10T20:30:51Z",
                            "uri": "http://an.archive.org/20080410203051/http://foo.bar/"
                        },
                        {
                            "datetime": "2012-08-31T12:22:34Z",
                            "uri": "http://an.archive.org/20120831122234/http://foo.bar/"
                        }
                    ]
                }
            }
            """
        ]

    elif req.startswith('/timemap1'):
        body = [
            """
            {
                "original_uri": "http://example.com/",
                "timegate_uri": "http://an.archive.org/timegate/http://example.com/",
                "timemap_uri": {
                    "json_format": "http://an.archive.org/timemap/2/json/http://example.com/",
                    "link_format": "http://an.archive.org/timemap/2/link/http://example.com/"
                },
                "mementos": {
                    "first": {
                        "datetime": "2003-05-13T00:00:13Z",
                        "uri": "http://an.archive.org/20030513000013/http://example.com/"
                    },
                    "last": {
                        "datetime": "2006-10-05T20:30:51Z",
                        "uri": "http://an.archive.org/20061005203051/http://example.com/"
                    },
                    "all": [
                        {
                            "datetime": "2003-05-13T00:00:13Z",
                            "uri": "http://an.archive.org/20030513000013/http://example.com/"
                        },
                        {
                            "datetime": "2005-04-10T07:05:12Z",
                            "uri": "http://an.archive.org/20050410070512/http://example.com/"
                        },
                        {
                            "datetime": "2006-10-05T20:30:51Z",
                            "uri": "http://an.archive.org/20061005203051/http://example.com/"
                        }
                    ]
                },
                "pages": {
                    "prev": {
                        "from": "2000-06-21T04:41:56Z",
                        "until": "2003-05-12T22:25:15Z",
                        "uri": "http://an.archive.org/timemap/1/json/http://example.com/"
                    },
                    "next": {
                        "from": "2006-10-06T00:00:57Z",
                        "until": "2009-04-10T23:45:20Z",
                        "uri": "http://an.archive.org/timemap/3/json/http://example.com/"
                    }
                }
            }
            """
        ]

    elif req.startswith('/timemap2'):
        body = [
            """
            {
                "original_uri": "http://another.com/",
                "timegate_uri": "http://an.archive.org/timegate/http://example.com/",
                "timemap_uri": {
                    "json_format": "http://an.archive.org/timemap/2/json/http://example.com/",
                    "link_format": "http://an.archive.org/timemap/2/link/http://example.com/"
                },
                "mementos": {
                    "first": {
                        "datetime": "2003-05-13T00:00:13Z",
                        "uri": "http://an.archive.org/20030513000013/http://example.com/"
                    },
                    "last": {
                        "datetime": "2006-10-05T20:30:51Z",
                        "uri": "http://an.archive.org/20061005203051/http://example.com/"
                    },
                    "all": [
                        {
                            "datetime": "2003-05-13T00:00:13Z",
                            "uri": "http://an.archive.org/20030513000013/http://another.com/"
                        },
                        {
                            "datetime": "2005-04-10T07:05:12Z",
                            "uri": "http://an.archive.org/20050410070512/http://another.com/"
                        },
                        {
                            "datetime": "2006-10-05T20:30:51Z",
                            "uri": "http://an.archive.org/20061005203051/http://another.com/"
                        }
                    ]
                },
                "pages": {
                    "prev": {
                        "from": "2000-06-21T04:41:56Z",
                        "until": "2003-05-12T22:25:15Z",
                        "uri": "http://an.archive.org/timemap/1/json/http://example.com/"
                    },
                    "next": {
                        "from": "2006-10-06T00:00:57Z",
                        "until": "2009-04-10T23:45:20Z",
                        "uri": "http://an.archive.org/timemap/3/json/http://example.com/"
                    }
                }
            }
            """
        ]

    elif req.startswith('/invalid'):
        status = '200 OK'
        body = ['{invalid json']

    else:
        status = '404 Not Found'
        body = ['{}']



    start_response(status, headers)
    return body