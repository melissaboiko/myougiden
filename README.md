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

    $ bin/updatedb-myougiden -f -d
    # alternatively: download JMdict_e.gz, run updatedb-myougiden -j JMdict_e.gz

    $ bin/myougiden -h # help
    $ bin/myougiden "tea ceremony" # try to guess what to query
    $ bin/myougiden 茶
    $ bin/myougiden -p 茶 # include partial matches
    $ bin/myougiden -t -x '茶.' # regexp search; tab-separated, one-line output
  