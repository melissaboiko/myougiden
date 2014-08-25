import os
import re
from glob import glob
import sqlite3 as sql

from myougiden import config
from myougiden.texttools import get_regexp
from myougiden.color import fmt
import myougiden.common

def regexp_sensitive(pattern, field):
    '''SQL hook function for case-sensitive regexp matching.'''
    reg = get_regexp(pattern, 0)
    return reg.search(field) is not None

def regexp_insensitive(pattern, field):
    '''SQL hook function for case-insensitive regexp matching.'''
    reg = get_regexp(pattern, re.I)
    return reg.search(field) is not None

#def match_word_sensitive(word, field):
#    '''SQL hook function for whole-word, case-sensitive, non-regexp matching.'''
#
#    reg = get_regexp(r'\b' + re.escape(word) + r'\b', 0)
#    return reg.search(field) is not None
#
#def match_word_insensitive(word, field):
#    '''SQL hook function for whole-word, case-sensitive, non-regexp matching.'''
#
#    reg = get_regexp(r'\b' + re.escape(word) + r'\b', re.I)
#    return reg.search(field) is not None

class DatabaseAccessError(Exception):
    '''Generic error accessing database.'''
    pass

class DatabaseMissing(DatabaseAccessError):
    '''Database not found.'''
    pass
class DatabaseWrongVersion(DatabaseAccessError):
    '''Database is of wrong version.'''
    pass
class DatabaseStaleUpdates(DatabaseAccessError):
    '''Temporary files left, updating process aborted anormally.'''
    pass

def test_database_tempfiles():
    '''Return values:

       - None: no temp file.
       - 'updating': updatedb-myougiden seems to be running.
       - 'stale': updatedb-myougiden seems to have been interrupted.
    '''

    temps = glob(config.get('paths','database') + '.new.*')
    if temps:
        for temp in temps:
            m = re.match(config.get('paths','database') + '.new.([0-9]*)',
                         temp)
            pid = int(m.group(1))
            try:
                os.getpgid(pid)
            except OSError:
                return 'stale'
        return 'updating'
    return None

def opendb(case_sensitive=False):
    '''Test and open SQL database; returns (con, cur).

    Raises DatabaseAccessError subclass if database can't be used for any
    reason.'''

    temps = test_database_tempfiles()
    if temps == 'stale':
        raise DatabaseStaleUpdates('updatedb-myougiden was interrupted; please run again')
    elif temps == 'updating':
        print("%s: updatedb-myougiden is running, please wait a while :)" %
              fmt('WARNING', 'warning'))

    if not os.path.isfile(config.get('paths','database')):
        raise DatabaseMissing('Could not find ' + config.get('paths','database'))

    try:
        con = sql.connect(config.get('paths','database'))
        cur = con.cursor()
    except sql.OperationalError as e:
        raise DatabaseAccessError(str(e))

    try:
        execute(cur, ('SELECT dbversion FROM versions;'))
        dbversion = cur.fetchone()[0]
    except sql.OperationalError:
        raise DatabaseAccessError("Couldn't read database to check version")

    if dbversion != config.get('core','dbversion'):
        raise DatabaseWrongVersion('Incorrect database version: %s' % dbversion)

    if case_sensitive:
        con.create_function('regexp', 2, regexp_sensitive)
        # con.create_function('match', 2, match_word_sensitive)
        execute(cur, 'PRAGMA case_sensitive_like = 1;')
    else:
        con.create_function('regexp', 2, regexp_insensitive)
        # con.create_function('match', 2, match_word_insensitive)
        execute(cur, 'PRAGMA case_sensitive_like = 0;')

    return con, cur

def execute(cur, *args):
    if myougiden.common.debug:
        print(*args)
    cur.execute(*args)
