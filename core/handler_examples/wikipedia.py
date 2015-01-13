import re

__author__ = 'Yorick Chollet'

from core.handler_examples.mediawiki import MediaWikiHandler


class WikipediaHandler(MediaWikiHandler):

    def __init__(self):
        MediaWikiHandler.__init__(self)