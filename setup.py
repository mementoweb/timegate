# -*- coding: utf-8 -*-
#
# This file is part of TimeGate.
# Copyright (C) 2016 CERN.
#
# TimeGate is free software; you can redistribute it and/or modify
# it under the terms of the Revised BSD License; see LICENSE file for
# more details.

"""A Memento TimeGate."""

import os
import sys

from setuptools import find_packages, setup

readme = open('README.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
    'httpretty>=0.8.14',
    'mock>=2.0.0',
]

extras_require = {
    ':python_version<"3.0"': [
        'ConfigParser>=3.3.0r2',
    ],
    'docs': [
        'Sphinx>=1.3',
    ],
    'uwsgi': [
        'uWSGI>=2.0.3',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for key, reqs in extras_require.items():
    if key[0] == ':':
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'pytest-runner>=2.6.2',
]

install_requires = [
    'LinkHeader>=0.4.3',
    'lxml>=3.4.1',
    'python-dateutil>=2.1',
    'requests>=2.2.1',
    'werkzeug>=0.9.6',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('timegate', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='timegate',
    version=version,
    description=__doc__,
    long_description=readme,
    keywords='memento timegate',
    license='BSD',
    author='LANL',
    author_email='yorick.chollet@gmail.com',
    url='https://github.com/mementoweb/timegate',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'timegate.handlers': [
            'arxiv = timegate.examples.arxiv:ArxivHandler',
            'aueb = timegate.examples.aueb:AuebHandler',
            'can = timegate.examples.can:CanHandler',
            'cat = timegate.examples.cat:CatHandler',
            'cr = timegate.examples.cr:CrHandler',
            'es = timegate.examples.es:EsHandler',
            'github = timegate.examples.github:GithubHandler',
            'gitlab = timegate.examples.gitlab:GitlabHandler',
            'loc = timegate.examples.loc:LocHandler',
            'mediawiki = timegate.examples.mediawiki:MediawikiHandler',
            'nara = timegate.examples.nara:NaraHandler',
            'orain = timegate.examples.orain:OrainHandler',
            'pastpages = timegate.examples.pastpages:PastpagesHandler',
            'po = timegate.examples.po:PoHandler',
            'sg = timegate.examples.sg:SgHandler',
            'si = timegate.examples.si:SiHandler',
            'simple = timegate.examples.simple:ExampleHandler',
            'w3c = timegate.examples.w3c:W3cHandler',
            'webcite = timegate.examples.webcite:WebCiteHandler',
            'wikia = timegate.examples.wikia:WikiaHandler',
            'wikipedia = timegate.examples.wikipedia:WikipediaHandler',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
