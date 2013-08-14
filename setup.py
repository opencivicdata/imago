#!/usr/bin/env python
from setuptools import setup, find_packages
from imago import __version__

setup(name='imago',
      version=__version__,
      packages=find_packages(),
      author="James Turk",
      author_email="jturk@sunlightfoundation.com",
      license="BSD",
      url='http://github.com/openscivicdata/imago/',
      description='Open Civic Data API',
      long_description='',
      platforms=['any'],
      install_requires=[
          'pymongo>=2.5',
          'Django>=1.5',
      ])
