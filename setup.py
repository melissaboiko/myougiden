#!/usr/bin/env python3
import subprocess
import os
import re
from configparser import ConfigParser
from distutils.command.install import install
from distutils.core import setup

dirname = os.path.dirname(__file__)
if dirname != '':
    os.chdir(os.path.dirname(__file__))

config = ConfigParser()
config.read('etc/config.ini')
version = config['core']['version']

def md_to_rest(f):
    '''Very hacky.'''

    s = ''
    for line in f:
        line = re.sub(r'!\[[^]]*\]\((.*)\)', r'\1', line)
        s += line

    s = s.replace(":\n\n", "::\n\n")
    return s

with open('README.md', 'r') as f:
    longdesc=md_to_rest(f)

setup(name='myougiden',
      version=version,
      description='Japanese/English command-line dictionary',
      long_description=longdesc,
      author='Leonardo Boiko',
      author_email='leoboiko@gmail.com',
      url='https://github.com/leoboiko/myougiden',
      packages=['myougiden'],
      scripts=['bin/myougiden', 'bin/updatedb-myougiden'],
      data_files=[('etc/myougiden/', ['etc/config.ini'])],
      license='GPLv3',
      install_requires=[
          'romkan',
          'termcolor',
          ],
      classifiers=[
          'Development Status :: 4 - Beta',
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

