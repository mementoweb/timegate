__author__ = 'Yorick Chollet'

from timegateerror import TimegateError


class HandlerError(TimegateError):

    def __init__(self, msg, status=503):
        super(HandlerError, self).__init__(msg, status)
