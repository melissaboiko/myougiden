#!/usr/bin/env python3
import subprocess
from distutils.command.install import install
from distutils.core import setup

# http://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script
class updatedb_install(install):
    def run(self):
        install.run(self)

        print("\nWill now attempt to create the database.")
        r = subprocess.call(['updatedb-myougiden', '-f', '-d'])
        if r == 0:
            print('Success in installing database! myougiden(1) ready to use.')
        else:
            print('ERROR: could not download & install database! myougiden cannot be used.')
            print('Try running "updatedb-myougiden -f -d" and see what happens.')

        print('''
Edict/JMdict is a frequently updated project. If you want to keep up
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
     )

