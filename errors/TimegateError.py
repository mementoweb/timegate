__author__ = 'Yorick Chollet'


class TimegateError(Exception):

    def __init__(self, msg, status):
        self.status = status
        super(TimegateError, self).__init__(msg)
