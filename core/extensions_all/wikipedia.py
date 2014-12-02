import re

__author__ = 'Yorick Chollet'

from core.extensions_all.mediawiki import MediaWikiHandler


class WikipediaHandler(MediaWikiHandler):


    def __init__(self):
        MediaWikiHandler.__init__(self)
        # Local fields, the uri pattern of a resource
        self.rex = re.compile('(.+)(/wiki/)(.+)')

        self.api_part = '/w/api.php'
        self.mementos_part = '/w/index.php'