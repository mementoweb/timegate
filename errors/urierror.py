__author__ = 'Yorick Chollet'

from timegateerror import TimegateError


class URIRequestError(TimegateError):

    def __init__(self, msg, status=400):
        super(URIRequestError, self).__init__(msg, status)
