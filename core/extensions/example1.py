__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.handlererror import HandlerError


class ExampleHandler(Handler):


    def __init__(self):

        # Regular Expressions of original resources that the Handler manages
        self.resources = ['https?://www.example.com/',
                          'https?://archive.example.com/resource/']

        # Boolean indicating if the handler can only request one Memento at a time
        self.singleonly = False

    def getall(self, uri):
        """
        Handler get method.
        :param uri: The original resource URI for which we need a Memento or a TimeMap
        :return:
            - None if the handler does not find any Memento for the requested resource
            - (URI, Datetime) strings tuple if one Memento is returned (basic case for singleonly)
            - [(URI, Datetime)] strings tuple array if several Memento are
            returned. The tuple (URI-R, None) can be used to differentiate
            between the original resource URI and Mememtos
        """

        # Example API URI
        api_uri = 'http://127.0.0.1:9001/timemap1/'
        # Requests the API
        response = self.request(uri, api_uri)

        # Handles API Response
        if response.status_code == 404:
            raise HandlerError("Cannot find resource on version server.", 404)

        elif response.status_code == 200:
            # Assume the API handles the requests correctly
            assert (response.headers['content-type'].startswith('application/json'))

            # Extract the JSON elements URI-R and (Mementos, Datetime) pairs
            json = response.json()
            uri_r = json['original_uri']
            dict_list = json['mementos']['all']

            # Transform each dictionary element e of the list into a tuple of its values
            def keys2tuple(e):
                return tuple(e.values())
            tuplelist = map(keys2tuple, dict_list)

            # Returns the list of tuples (URI, Datetime)
            tuplelist.append((uri_r, None))
            return tuplelist

        else:
            # API response undefined.
            raise HandlerError("Unknown API response.", 503)
