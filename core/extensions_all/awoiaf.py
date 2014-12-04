import re

__author__ = 'Yorick Chollet'

from core.extensions_all.mediawiki import MediaWikiHandler


class AWOIAFHandler(MediaWikiHandler):


    def __init__(self):
        MediaWikiHandler.__init__(self)

        # Local fields, the uri pattern of a resource
        self.rex = re.compile('(.+)(/index.php/)(.+)')

        self.api_part = '/api.php'
        self.mementos_part = '/index.php'
