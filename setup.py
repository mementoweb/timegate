__author__ = 'Yorick Chollet'
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='timegate',
      version='0.1.0',
      author='Yorick Chollet',
      author_email="yorick.chollet@gmail.com",
      url="https://github.com/mementoweb/timegate",
      download_url="https://github.com/mementoweb/timegate/releases",
      description="A Generic Memento TimeGate",
      long_description=read('README.md'),
      packages=[
          'timegate'
      ],
      keywords="timegate memento uwsgi python",
      license='http://mementoweb.github.io/SiteStory/license.html',
      install_requires=[
          "uWSGI>=2.0.3",
          "requests>=2.2.1"
      ],
      # tests_require=[
      #     'WebTest>=2.0.14'
      # ],
      # test_suite='test',
      scripts=['bin/timegate'],
      include_package_data=True,
      zip_safe=False,
      data_files=[('/etc/timegate', ['conf/timegate.ini'])
                  # ('db', ['db/subscriptions.pk']), TODO cache
                  ]
      )