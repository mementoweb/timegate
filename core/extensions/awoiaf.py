import re

__author__ = 'Yorick Chollet'

from core.extensions_utils.mediawiki import MediaWikiHandler


class AWOIAFHandler(MediaWikiHandler):


    def __init__(self):
        MediaWikiHandler.__init__(self)
        # Mandatory fields
        self.resources = ['http://awoiaf.westeros.org/index.php/.+']

        self.base = 'http://awoiaf.westeros.org/index.php/'

        # Local fields, the uri pattern of a resource
        self.rex = re.compile('(.+)(/index.php/)(.+)')

        self.api_part = '/api.php'
        self.mementos_part = '/index.php'
