Currently, this is a barely functional command-line interface for
EDICT (JMdict), the Japanese-English collaborative dictionary.
Perhaps one day it will be useable (or not).

It translates EDICT to sqlite3. This costs some disk space, but with
indexes, it seems to be reasonably fast.

If you'd like to try it:

    $ git clone git://github.com/leoboiko/myougiden.git
    $ cd myougiden

    $ ./updatedb.py -f
    # this generates jmdict.sqlite
    # you can delete JMdict_e.gz if you want

    $ ./myougiden -h # help
  