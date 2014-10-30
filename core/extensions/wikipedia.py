import re
import logging

__author__ = 'Yorick Chollet'

from core.extensions.mediawiki import MediaWikiHandler
from errors.handlererror import HandlerError

from tgutils import date_str


class WikipediaHandler(MediaWikiHandler):


    def __init__(self):
        MediaWikiHandler.__init__(self)
        # Mandatory fields
        self.resources = ['https?://[a-z]{2,3}.wikipedia.org/wiki/.+']
        # Local fields, the uri pattern of a resource
        self.rex = re.compile('(.+)(/wiki/)(.+)')

        self.api_part = '/w/api.php'
        self.mementos_part = '/w/index.php'