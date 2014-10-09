__author__ = 'Yorick Chollet'

from timegateerror import TimegateError


class DateTimeError(TimegateError):

    def __init__(self, msg, status=400):
        super(DateTimeError, self).__init__(msg, status)
