myougiden is a command-line, Japanese/English English/Japanese dictionary.
It's based on EDICT (JMdict), the venerable collaborative project.  It's
currently functional, if a bit (a lot) rough in the edges.

Features:
 - Fully Unicode-aware.
 - Regular expression support.
 - Partial, full, whole-word, and start-of-field queries.
 - Intelligently figure out what kind of query is intended.
 - Optional rōmaji input and output.
 - Option for tab-separated output, easily manipulable with Unix tools. (beta)
 - Full color output, including partial match highlighting.  No seriously, this
   thing has a *lot* of color.  I mean we're talking Takashi Murakami material
   right here.
 - Displays JMdict restricted readings and senses.
 - Auto-pager, auto-color, auto-nice, auto-greppable output, and other small
   niceties.

myougiden saves EDICT data in sqlite3 format. This costs some
disk space (currently about 53MiB), but with indexes, it seems to
be reasonably fast.

Sample usage
============

Some example queries:

    $ myougiden tea ceremony      # guess what kind of query to run
    $ myougiden 茶                # ibid
    $ myougiden chanoyu           # if no match is found, treat as rōmaji
    $ myougiden -r kanji          # forces rōmaji

    $ myougiden -w flower tea     # word search; return matches including both
    $ myougiden -w flower -tea    # matches include word 'flower' but not 'tea'
    $ myougiden -w 'tea ceremony' # matches include the phrase in this order

    $ myougiden -b 茶             # beggining word search; starts with 茶

    $ myougiden -p 茶             # partial match anywhere
    $ myougiden -p -f 茶          # ...but limit to frequent words
    $ myougiden -p -f -t 茶       # ...and tab-separated, single-line output

    $ myougiden -x '茶$'          # regexp search

    $ myougiden -h                # long help
    $ myougiden -a uK             # consult documentation for abbreviations

Screenshots
===========

![myougiden screenshot](http://namakajiri.net/pics/screenshots/myougiden.png)

Installation
============

myougiden needs Python 3 and pip.  In Debian/Ubuntu, you can
install them like this:

    $ sudo apt-get install python3 python3-pip

Then install myougiden using pip:

    $ sudo pip-3.2 install myougiden # use your version

Then, you need to compile the dictionary database at least once:

    $ sudo updatedb-myougiden -f
    # This command downloads and compile JMdict.
    # It's a bit slow, go have some coffee...

That's it, have fun!

EDICT/JMdict is a frequently updated dictionary.  If you'd like
to keep up with new entries and corrections, consider adding
`updatedb-myougiden -f` to cron (for example, in
/etc/cron.weekly/myougiden ).

Upgrading
---------

Just upgrade the pip package:

    $ sudo pip install --upgrade myougiden

Installing in Debian squeeze
----------------------------

As of this writing, Debian squeeze has no python3-pip.  You can
install it manually like this:

    $ sudo apt-get install python3.1 curl
    $ curl -O http://python-distribute.org/distribute_setup.py
    $ sudo python3.1 distribute_setup.py
    $ curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    $ sudo python3.1 get-pip.py

Now you have a pip-3.1 to install any python3 pip packages!

Python ≤ 3.1 needs the package `argparse` :

    $ sudo pip-3.1 install argparse

Finally, install as above:

    $ sudo pip-3.1 install myougiden
    $ sudo updatedb-myougiden -f

Installing from sources
-----------------------

Required software:
 - Python 3
 - rsync (recommended)

Required python packages (available on pip):
 - romkan
 - termcolor
 - argparse (only for Python ≤ 3.1)
 - psutil (recommended; only for Python ≤ 3.2)

To install from github:

    $ git clone git://github.com/leoboiko/myougiden.git
    $ cd myougiden
    $ sudo python3 setup.py install

