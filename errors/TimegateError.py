__author__ = 'Yorick Chollet'


class TimegateError(Exception):

    def __init__(self, msg, status):
        self.status = status
        super(TimegateError, self).__init__(msg)

class TimeoutError(TimegateError):

    def __init__(self, msg, status=413):
        super(TimegateError, self).__init__(msg, status)
