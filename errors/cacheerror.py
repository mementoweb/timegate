__author__ = 'Yorick Chollet'

from timegateerror import TimegateError


class CacheError(TimegateError):

    def __init__(self, msg, status=500):
        super(CacheError, self).__init__(msg, status)
