"""
Example handler
"""
__author__ = "Yorick Chollet"

# Mandatory
from core.handler_baseclass import Handler

# For get_memento() date parameter
import datetime

# For custom errors sent to client
from errors.timegateerrors import HandlerError


class ExampleHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        # Initialization code here. This part is run only once
        versions_a = [
            'http://www.example.com/resourceA_v1',
            'http://www.example.com/resourceA_v2',
            'http://www.example.com/resourceA_v3'

        ]
        date_times_a = [
            '1999-09-30T01:50:50Z',
            '2010-10-16T13:27:27Z',
            '2015-01-03T22:00:00Z'
        ]
        versions_b = [
            'http://www.example.com/resourceB_v1',
            'http://www.example.com/resourceB_v2',

        ]
        date_times_b = [
            '1998-07-17T17:47:31Z',
            '2000-11-08T19:05:09Z'
        ]
        self.archives = {
            'http://www.example.com/resourceA': versions_a,
            'http://www.example.com/resourceB': versions_b
        }
        self.dates = {
            'http://www.example.com/resourceA': date_times_a,
            'http://www.example.com/resourceB': date_times_b

        }

    # This is the function to implement.
    def get_all_mementos(self, uri_r):
        # Verifies and processes the requested URI
        archived_uris = self.archives.keys()
        if uri_r in archived_uris:
            # Contact the API to retrieve the list of URI-Ms for this URI-R along with their datetimes

            # In this example, everything is done in a statically
            # But this is where the handler is supposed to access the versions API
            uri_ms = self.archives[uri_r]
            datetimes = self.dates[uri_r]

            # Generate the list of tuples [(uri_string, date_string)]
            tuple_list = zip(uri_ms, datetimes)
            return tuple_list  # A list of tuple containing all Mementos is returned
        else:
            # No Memento for this uri was found in archive
            return []

    # Implement this function instead to bypass the TimeGate's best Memento selection algorithm.
    # Also, it can be used if the whole list cannot be accessed easily.
    # If both get_all_mementos() and get_memento() are implemented. get_memento() will always be preferred by the TimeGate.
    def get_memento(self, uri_r, req_datetime):
        # Suppose you have a special rule for certain dates
        if req_datetime.year < 1999:
            # In this case, we do not serve anything before 2001
            # Return a custom Error to the client
            raise HandlerError("Cannot server a Memento before 1999", status=404)
        else:
            # Gets all mementos for this URI
            mementos_list = self.get_all_mementos(uri_r)

            # Find the best single memento is returned for this uri_r and this date
            (uri_m, date_time) = mementos_list[-1]
            # In this example we take the last one

            return (uri_m, date_time)  # The return value is a tuple here.


