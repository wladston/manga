#!/usr/bin/env python

import sys
import os
from distutils.core import setup

if sys.version_info < (3,0):
    raise NotImplementedError("Sorry, you need Python 3.x to use manga.")

import manga

setup(name='manga',
      version=manga.__version__,
      description='Data abstraction layer for MongoDB.',
      long_description=manga.__doc__,
      author=manga.__author__,
      author_email='wladston@wladston.net',
      url='http://github.com/wladston/manga/',
      py_modules=['manga'],
      scripts=['manga.py'],
      license='MIT',
      platforms = 'any',
      classifiers=['Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Database',
        'Programming Language :: Python :: 3',
        ],
     )
