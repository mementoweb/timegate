import constants

__author__ = 'Yorick Chollet'


def application(env, start_response):
    """
    WSGI application object.
    :param env: Dictionary containing environment variables from the client request
    :param start_response: Callback function used to send HTTP status and headers to the server.
    :return: The response body.
    """

    status = 200
    body = ["It works!"]
    headers = [('Content-Type', 'text/html')]

    start_response(constants.HTTP_STATUS[status], headers)
    return body
