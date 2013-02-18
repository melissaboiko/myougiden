myougiden is an attempt at a command-line, Japanese/English
English/Japanese dictionary.  It's based on EDICT (JMdict), the
venerable collaborative project.  It's currently functional, but
bare-bones; perhaps one day it'll grow useable (or not).

myougiden saves EDICT data in sqlite3 format. This costs some disk
space (currently about 50MiB), but with indexes, it seems to be
reasonably fast.

If you'd like to try it, you need python 3 and pip:

    $ sudo apt-get install python3 python3-pip
    $ sudo pip install myougiden

Then, you need to compile the dictionary database at least once:

    $ sudo updatedb-myougiden -f
    $ # go have some coffee...

Sample usage:

    $ myougiden -h # long help
    $ myougiden "tea ceremony" # try to guess what to query
    $ myougiden 茶
    $ myougiden -p 茶 # include partial matches
    $ myougiden -x -t '茶.' # regexp search; tab-separated, one-line output

