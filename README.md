myougiden is an attempt at a command-line, Japanese/English
English/Japanese dictionary.  It's based on EDICT (JMdict), the
venerable collaborative project.  It's currently functional, but
bare-bones.

Features:
 - Fully Unicode-aware.
 - Regular expression support.
 - Partial, full, and whole-word queries.
 - Optional rōmaji input and output.
 - Intelligently find out what kind of query is intended.
 - Full color output, highlighting matches.
 - Option for tab-separated output, easily manipulable with Unix tools.

myougiden saves EDICT data in sqlite3 format. This costs some
disk space (currently about 52MiB), but with indexes, it seems to
be quite fast.

Sample usage
============

Some example queries:

    $ myougiden -h             # long help
    $ myougiden tea ceremony   # guess what to query
    $ myougiden 茶             # ibid
    $ myougiden -p 茶          # include partial matches
    $ myougiden -p -f 茶       # ...but limit to frequent words
    $ myougiden -p -f -t 茶    # ...and tab-separated, single-line output
    $ myougiden -x '茶.'       # regexp search
    $ myougiden sakura         # if no match is found, treat as rōmaji
    $ myougiden -r kanji       # forces rōmaji

Installation
============

myougiden needs Python 3 and pip.  In Debian/Ubuntu, you can
install them like this:

    $ sudo apt-get install python3 python3-pip

Then install myougiden using pip:

    $ sudo pip-3.2 install myougiden # use your version

Then, you need to compile the dictionary database at least once:

    # This command downloads and compile JMdict. It's a bit heavy...
    $ sudo updatedb-myougiden -f
    # go have some coffee...

That's it, have fun!

EDICT/JMdict is a frequently updated dictionary.  If you'd like
to keep up with new entries and corrections, consider adding
`updatedb-myougiden -k -f` to cron (for example, in
/etc/cron.weekly/myougiden ).

Upgrading
---------

Just upgrade the pip package:

    $ sudo pip install --upgrade myougiden

Installing in Debian stable
---------------------------

As of this writing, Debian squeeze has no python3-pip.  You can
install it manually like this:

    $ sudo apt-get install python3.1 curl
    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python3.1 distribute_setup.py
    $ curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    $ sudo python3.1 get-pip.py

Now you have a pip-3.1 to install any python3 pip packages!

Python < 3.1 needs the package `argparse` :

    $ sudo pip-3.1 install argparse

Finally, install as above:

    $ sudo pip-3.1 install myougiden
    $ sudo updatedb-myougiden -f

Installing from sources
-----------------------

Required python packages (available on pip):

 - romkan
 - termcolor
 - argparse (only for Python ≤ 3.1)

To install from github:

    $ git clone git://github.com/leoboiko/myougiden.git
    $ cd myougiden
    $ sudo python3 setup.py install

