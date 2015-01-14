__author__ = 'Yorick Chollet'

from StringIO import StringIO
import logging

from lxml import etree
import re

from core.handler_baseclass import Handler
from errors.timegateerrors import HandlerError


class ArxivHandler(Handler):

    def __init__(self):
        Handler.__init__(self)

        # Resources

        # Ignores all that trails the identifier (? params, vX version,...)
        self.rex = re.compile(r'(http://arxiv.org)/((?:pdf)|(?:abs))/(\d+\.\d+)(.*)')
        self.api_base = 'http://export.arxiv.org/oai2'

    def get_all_mementos(self, uri_r):
        try:
            # Extract the resource ID
            match = self.rex.match(uri_r)
            parts = match.groups()
            base = parts[0]
            type = parts[1]
            resource = parts[2]
            normalized_uri = '%s/%s/%s' % (base, type, resource)

            # Prepars the API call
            params = {
                'verb': 'GetRecord',
                'identifier': 'oai:arXiv.org:%s' % resource,
                'metadataPrefix': 'arXivRaw'
            }

            # Queries the API and extract the values
            response = self.request(self.api_base, params=params)
            if not response:
                raise HandlerError("API response not 2XX", 404)
            root = etree.parse(StringIO(response.content), etree.XMLParser(recover=True))
            versions = root.findall('.//{http://arxiv.org/OAI/arXivRaw/}version')

            # Processes the return
            def mapper(version):
                v = version.xpath('@*')[0]
                date = version.find('./{http://arxiv.org/OAI/arXivRaw/}date').text
                return (normalized_uri + v, date)

            return map(mapper, versions)

        except Exception as e:
            logging.debug('Arxiv handler exception: %s returning 404' % e.message)
            raise HandlerError('Resource Not Found on arXiv server', 404)
