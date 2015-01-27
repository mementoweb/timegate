__author__ = 'Yorick Chollet'

import logging

from core.handler_baseclass import Handler
from errors.timegateerrors import HandlerError


class PastpagesHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.LIMIT_MAX = 100
        self.BASE = 'http://www.pastpages.org'
        self.API_TIMEFMT = '%Y-%m-%dT%H:%M:%S'

        # Building pages list of ('uri', 'slug') pairs
        self.pages_list = []

        try:
            params = {
                'limit': self.LIMIT_MAX
            }
            request = '/api/beta/sites/'
            has_next = True

            # Keep while there are still result pages
            while has_next:
                json_response = self.request(self.BASE+request, params=params).json()

                self.pages_list.extend([
                    # 'objects' is the list of responses
                    # 'objects.url' and 'objects.slug' are the URI and the website's short name respectively
                    (obj['url'], obj['slug'])
                        for obj in json_response['objects']
                ])

                request = json_response['meta']['next']
                params = None  # the request already contains &limit and &offset
                has_next = request is not None # Each response has a non null 'meta.next' value if it has a continuation

        except Exception as e:
            logging.critical("Cannot create the handler's page list:")
            raise e

        logging.info("Found %s websites on pastpages' API." % len(self.pages_list))

    def get_memento(self, uri_r, req_datetime):
        matches = [x for x in self.pages_list if uri_r.startswith(x[0])]
        if len(matches) == 0:
            raise HandlerError("Pastpages does not have archives of that website.", 404)
        if len(matches) > 1:
            logging.error("Uri conflict in pastpages' API URI list.")
            raise HandlerError("Error in pastpages API")

        site_slug = matches[0][1]
        params = {
            'limit': 1,
            'site__slug': site_slug,
            'timestamp__lte': req_datetime.strftime(self.API_TIMEFMT)
        }

        request = '/api/beta/screenshots/'

        json_response = self.request(self.BASE+request, params=params).json()

        image = [
            # 'objects' is the list of responses
            # 'objects.absolute_url' is the URI. It exists if 'objects.has_image'
            (self.BASE+obj['absolute_url'], obj['timestamp'])
                for obj in json_response['objects']
        ][0]

        return image

    def get_all_mementos(self, uri_r):
        # WILL BE TOO SLOW. TOO MANY WEBSITES

        matches = [x for x in self.pages_list if uri_r.startswith(x[0])]
        if len(matches) == 0:
            raise HandlerError("Pastpages does not have archives of that website.", 404)
        if len(matches) > 1:
            logging.error("Uri conflict in pastpages' API URI list.")
            raise HandlerError("Error in pastpages API")

        site_slug = matches[0][1]
        params = {
            'limit': self.LIMIT_MAX,
            'site__slug': site_slug
        }
        request = '/api/beta/screenshots/'
        has_next = True

        image_list = []
        # Keep while there are still result pages
        while has_next:
            json_response = self.request(self.BASE+request, params=params).json()

            image_list.extend([
                # 'objects' is the list of responses
                # 'objects.image' is the URI of the memento. It exists if 'objects.has_image'
                (obj['image'], obj['timestamp'])
                    for obj in json_response['objects'] if obj['has_image']
            ])

            request = json_response['meta']['next']
            params = None  # the request already contains &limit and &offset
            has_next = request is not None # Each response has a non null 'meta.next' value if it has a continuation

        return image_list