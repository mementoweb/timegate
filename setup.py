__author__ = 'Yorick Chollet'
import os
try:
    from setuptools import setup
    from setuptools import find_packages
except ImportError:
    from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='timegate',
      version='0.1.1',
      author='Yorick Chollet',
      author_email='yorick.chollet@gmail.com',
      url='https://github.com/mementoweb/timegate',
      download_url='https://github.com/mementoweb/timegate/releases',
      description="A Generic Memento TimeGate",
      long_description=read('README.md'),
      packages=find_packages(exclude=['doc.*']),
      keywords='timegate memento uwsgi python',
      license='http://mementoweb.github.io/SiteStory/license.html',
      install_requires=[
          'uWSGI>=2.0.3',
          'ConfigParser>=3.3.0r2',
          'python-dateutil>=2.1',
          'requests>=2.2.1',
          'werkzeug>=0.9.6'

      ],
      include_package_data=True,
      zip_safe=False
      )