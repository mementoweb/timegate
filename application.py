from dateutil import parser

from conf.constants import URI_PARTS as URI
from conf.constants import HTTP_STATUS as HTTP
from errors.date_error import DateRequestError


__author__ = 'Yorick Chollet'

debug = False


def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    # Debug prints
    if debug:
        print("ENV: \n %s" % env)

    # Extracting requested values
    req_path = env.get("PATH_INFO")
    req_datetime = env.get("HTTP_ACCEPT_DATETIME")

    # Standard Response
    status = 404
    body = ["404 - Not Found \n    Req_path: %s \n" % req_path]
    headers = [('Content-Type', 'text/html')]

    # Processing request path
    req_type = str.split(req_path.strip('/'), '/', 1)[0]

    # TimeGate Logic
    if req_type == URI['G']:
        # Processing requested date
        try:
            accept_datetime = dateparser(req_datetime)
        except DateRequestError as dre:
            body = ["400 - Bad Request"
                    "\n    Unable to parse: %s \n" % req_datetime]
            start_response(HTTP[400], headers)
            return body

        body = ['Req Path: %s '
                '\nReq time: %s \n' % (req_path, accept_datetime)]
        status = 200

    # TimeMap Logic
    elif req_type == URI['T']:
        body = ["400 - Bad request. Timemap not implemented yet \n"]
        status = 400

    # TestCase Logic
    elif req_type == "test":
        body = ["server running"]
        status = 200

    else:
        print "URI type does not match"

    # Standard response
    start_response(HTTP[status], headers)
    return body


def dateparser(datestr):
    try:
        date = parser.parse(datestr)
        return date
    except Exception as e:
        raise DateRequestError(e.message)

