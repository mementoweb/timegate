__author__ = 'Yorick Chollet'

import logging

from datetime import datetime, timedelta
from dateutil.parser import parse as parse_datestr
from dateutil.tz import tzutc
from urlparse import urlparse

from conf.constants import DATEFMT, HTTPRE
from errors.urierror import URIRequestError
from errors.dateerror import DateTimeError


def validate_req_datetime(datestr, strict=True):
    """
    Parses the requested date string into a dateutil time object
    Raises DateTimeError if the parse fails to produce a datetime.
    :param datestr: A date string, in a common format.
    :return: the dateutil time object
    """
    try:
        if strict:
            date = datetime.strptime(datestr, DATEFMT)
        else:
            date = parse_datestr(datestr, fuzzy=True)
        logging.debug("Accept datetime parsed to: "+date_str(date))
        return date.replace(tzinfo=tzutc())
    except Exception as e:
        raise DateTimeError("Error parsing 'Accept-Datetime: %s' \n"
                            "Message: %s" % (datestr, e.message))


def validate_req_uri(pathstr, methodstr):
    """
    Parses the requested URI string.
    Raises URIRequestError if the parse fails to recognize a valid URI
    :param urlstr: A URI string, in a common format.
    :return: the URI string object
    """

    try:
        #removes leading 'method/' and replaces whitespaces
        path = pathstr[len(methodstr+'/'):].replace(' ', '%20')

        # Trying to fix incomplete URI
        if not bool(HTTPRE.match(path)):
            # if not bool(WWWRE.match(path)):
            #     path = 'www.'+path TODO remove?
            path = 'http://'+path

        uri = validate_uristr(path)
        logging.debug("Requested URI parsed to: "+uri)
        return uri
    except Exception as e:
        raise URIRequestError("Error: Cannot parse requested path '%s' \n"
                              "message: %s" % (pathstr, e.message))


def validate_uristr(uristr):
    try:
        return str(urlparse(uristr).geturl())
    except Exception as e:
        raise Exception("Error: cannot parse uri string %s" % uristr)

def validate_date(datestr, strict=False):
    try:
        if strict:
            date = datetime.strptime(datestr, DATEFMT)
        else:
            date = parse_datestr(datestr, fuzzy=True).replace(tzinfo=tzutc())
        return date
    except Exception as e:
        raise Exception("Error: cannot parse date string %s" % datestr)


def date_str(date):
    return date.strftime(DATEFMT)

def parse_date(*args, **kwargs):
    return parse_datestr(*args, **kwargs)

def nowstr():
    return date_str(datetime.utcnow()).encode('utf8')


def closest(timemap, accept_datetime, sorted=True):
    """
    Finds the chronologically closest memento
    :param timemap: A sorted Timemap
    :param accept_datetime: the time object
    :param sorted: boolean to indicate if the list is sorted or not.
    :return:
    """

    delta = timedelta.max
    memento = None

    for (url, dt) in timemap:
        diff = abs(accept_datetime - dt)
        if diff < delta:
            memento = url
            delta = diff
        elif sorted:
            # The list is sorted and the delta didn't increase this time.
            # It will not increase anymore: Return the Memento (best one).
            return memento

    return memento


def now():
    return datetime.utcnow().replace(tzinfo=tzutc())