__author__ = 'Yorick Chollet'


class TimegateError(Exception):

    def __init__(self, msg, status):
        self.status = status
        super(TimegateError, self).__init__(msg)


class TimeoutError(TimegateError):

    def __init__(self, msg, status=416):
        super(TimegateError, self).__init__(msg, status)


class URIRequestError(TimegateError):

    def __init__(self, msg, status=400):
        super(URIRequestError, self).__init__(msg, status)


class HandlerError(TimegateError):

    def __init__(self, msg, status=503):
        super(HandlerError, self).__init__(msg, status)


class DateTimeError(TimegateError):

    def __init__(self, msg, status=400):
        super(DateTimeError, self).__init__(msg, status)


class CacheError(TimegateError):

    def __init__(self, msg, status=500):
        super(CacheError, self).__init__(msg, status)
