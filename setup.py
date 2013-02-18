#!/usr/bin/env python3
import subprocess
import os
from distutils.command.install import install
from distutils.core import setup

# http://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script
class updatedb_install(install):
    def run(self):
        install.run(self)

        print("\nWill now attempt to create the database.")

        try:
            # add location of scripts just installed to PATH
            os.environ['PATH'] = self.install_scripts + ':' + os.environ['PATH']
            r = subprocess.call(['updatedb-myougiden', '-f', '-d'])
            if r != 0:
                raise RuntimeError("Command failed; exit status %d" % r)

            print('Success in installing database! myougiden(1) ready to use.')
        except Exception as e:
            print(e)
            print('ERROR: could not download & install database! myougiden cannot be used.')
            print('Try running "updatedb-myougiden -f -d" and see what happens.')

        print('''
Edict/JMdict is a frequently updated dictionary. If you want to keep up
with recent entries, try adding a call to "updatedb-myougiden -f -d"
to cron (for example in /etc/cron.weekly/myougiden ).
''')
        
setup(name='myougiden',
      version='0.1',
      description='Japanese/English command-line dictionary',
      author='Leonardo Boiko',
      author_email='leoboiko@gmail.com',
      url='https://github.com/leoboiko/myougiden',
      py_modules=['myougiden'],
      scripts=['bin/myougiden', 'bin/updatedb-myougiden'],
      cmdclass=dict(install=updatedb_install),
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

