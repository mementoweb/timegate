from urlparse import urlparse

from dateutil import parser

from conf.constants import HTTPRE, WWWRE
from conf.constants import URI_PARTS as URI
from conf.constants import HTTP_STATUS as HTTP
from errors.urierror import URIRequestError
from errors.dateerror import DateRequestError
from errors.timegateerror import TimegateError


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
    req_path = env.get("PATH_INFO", "/")
    req_datetime = env.get("HTTP_ACCEPT_DATETIME")

    # Standard Response
    status = 404
    message = "404 - Not Found \n"
    headers = [('Content-Type', 'text/html')]

    # Processing request path
    req_path = req_path.lstrip('/')
    req_type = req_path.split('/', 1)[0]

    # TimeGate Logic
    if req_type == URI['G']:
        # Processing request
        try:
            req_uri = req_path[len(req_type+'/'):] #removes leading timegate/
            accept_datetime = dateparse(req_datetime)
            parseduri = uriparse(req_uri)
        except TimegateError as e:
            return respond(e.status, e.message,
                           start_response, headers)

        body = ['Req Path: %s '
                '\nReq time: %s \n' % (parseduri.geturl(), accept_datetime)]
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
        message = "URI type does not match timegate or timemap"
        if debug:
            print "URI type does not match timegate or timemap"

    return respond(status, message, start_response, headers)


def dateparse(datestr):
    try:
        date = parser.parse(datestr)
        return date
    except Exception as e:
        raise DateRequestError("Error on Accept-Datetime: %s "
                               "\n \n details: %s" % (datestr, e.message))


#TODO whitespaces escapes
def uriparse(pathstr):
    """
    Parses the requested URI
    :param urlstr:
    :return:
    """
    if not pathstr:
        raise URIRequestError("Error: Empty path")

    # Trying to fix incomplete URI
    if not bool(HTTPRE.match(pathstr)):
        if not bool(WWWRE.match(pathstr)):
            pathstr = 'www.'+pathstr
        pathstr = 'http://'+pathstr

    try:
        parsed = urlparse(pathstr, scheme='http')
    except Exception as e:
        raise URIRequestError("Error: Cannot parse path: %s" % e.message)

    return parsed


def respond(status, message, start_response, headers):

    body = ["%s \n %s" % (status, message)]
    start_response(HTTP[status], headers)
    return body
