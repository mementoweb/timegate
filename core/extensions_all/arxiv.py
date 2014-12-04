__author__ = 'Yorick Chollet'

from core.handler import Handler
from errors.timegateerrors import HandlerError
from lxml import etree
from StringIO import StringIO
import logging
import re


class ArxivHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

        # Resources
        self.rex = re.compile('(http://arxiv.org)/((?:pdf)|(?:abs))/(.+)')
        self.api_base = 'http://export.arxiv.org/oai2'

    def get_all_mementos(self, uri_r):
        try:
            # Extract the resource ID
            match = self.rex.match(uri_r)
            if match.groups()[1] == 'pdf':
                uri_r = uri_r.replace('.pdf', '')
            match_normalized = self.rex.match(uri_r)
            parts = match_normalized.groups()
            resource = parts[2]

            # Prepars the API call
            params = {
                'verb': 'GetRecord',
                'identifier': 'oai:arXiv.org:%s' % resource,
                'metadataPrefix': 'arXivRaw'
            }

            # Queries the API and extract the values
            response = self.request(self.api_base, params=params)
            root = etree.parse(StringIO(response.content), etree.XMLParser(recover=True))
            versions = root.findall('.//{http://arxiv.org/OAI/arXivRaw/}version')

            # Processes the return
            def mapper(version):
                v = version.xpath('@*')[0]
                date = version.find('./{http://arxiv.org/OAI/arXivRaw/}date').text
                return (uri_r + v, date)

            return map(mapper, versions)

        except Exception as e:
            logging.debug('Arxiv handler exception: %s returning 404' % e.message)
            raise HandlerError('Resource Not Found on arXiv server', 404)
