__author__ = 'Yorick Chollet'

from timegateerror import TimegateError


class DateRequestError(TimegateError):

    def __init__(self, msg, status=400):
        super(DateRequestError, self).__init__(msg, status)
