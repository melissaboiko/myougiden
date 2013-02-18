myougiden is an attempt at a command-line, Japanese/English
English/Japanese dictionary.  It's based on EDICT (JMdict), the
venerable collaborative project.  It's currently functional, but
bare-bones; perhaps one day it'll grow useable (or not).

myougiden saves EDICT data in sqlite3 format. This costs some disk
space (currently about 50MiB), but with indexes, it seems to be
reasonably fast.

If you'd like to try it:

    $ git clone git://github.com/leoboiko/myougiden.git
    $ cd myougiden
    $ sudo python3 setup.py install
    $ myougiden -h # help
    $ myougiden "tea ceremony" # try to guess what to query
    $ myougiden 茶
    $ myougiden -p 茶 # include partial matches
    $ myougiden -x -t '茶.' # regexp search; tab-separated, one-line output

    $ # if you don't want to install, you can try it from the source dir:
    $ bin/updatedb-myougiden -f -d
    $ # alternatively: download JMdict_e.gz, do updatedb-myougiden -j JMdict_e.gz
    $ bin/myougiden -h # help
  