# Memento Cache Proxy for Google search engine.
# Authors: Ahmed AlSum aalsum@cs.odu.edu
#          Yorick Chollet yorick.chollet@gmail.com
# Dates: July 21, 2010. Edited Dec 1st, 2014

import re
from core.handler import Handler

__author__ = "aalsum, Yorick Chollet"


class GoogleHandler(Handler):

    def __init__(self):
        Handler.__init__(self)
        self.end_point = 'http://webcache.googleusercontent.com/search?q=cache:'
        self.dateExpression = re.compile(r"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{1,2}, (19|20)\d\d \d\d:\d\d:\d\d)")

    def get_all_mementos(self, req_url):

        final_url = self.end_point + req_url
        page = self.request(final_url).content
        changes = []

        # @type page str
        # This step is required to make sure we have a google cached page.
        if page.find('This is Google&#39;s cache of') > -1:

            result = self.dateExpression.search(page)
            if result:
                dtstr = result.group(0)
                changes.append((final_url, dtstr))

        return changes