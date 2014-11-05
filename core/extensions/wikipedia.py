import re

__author__ = 'Yorick Chollet'

from core.extensions_utils.mediawiki import MediaWikiHandler


class WikipediaHandler(MediaWikiHandler):


    def __init__(self):
        MediaWikiHandler.__init__(self)
        # Mandatory fields
        self.resources = ['https?://[a-z]{2,3}.wikipedia.org/wiki/.+']
        # Local fields, the uri pattern of a resource
        self.rex = re.compile('(.+)(/wiki/)(.+)')

        self.base = ''

        self.api_part = '/w/api.php'
        self.mementos_part = '/w/index.php'