#!/usr/bin/env python3
import subprocess
import os
from distutils.command.install import install
from distutils.core import setup

setup(name='myougiden',
      version='0.1.1',
      description='Japanese/English command-line dictionary',
      author='Leonardo Boiko',
      author_email='leoboiko@gmail.com',
      url='https://github.com/leoboiko/myougiden',
      py_modules=['myougiden'],
      scripts=['bin/myougiden', 'bin/updatedb-myougiden'],
      license='GPLv3',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Education',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English',
          'Natural Language :: Japanese',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3',
          'Topic :: Education',
          'Topic :: Text Processing :: Linguistic',
          ]
     )

