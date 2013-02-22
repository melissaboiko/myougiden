import errno
import sys
import os
import re
import romkan
import configparser

from myougiden import *
from myougiden.texttools import *
from myougiden.color import fmt

import myougiden

# from http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
# convenience function because python < 3.2 has no exist_ok
def mkdir_p(path):
    # safely allows mkdir_p(os.path.dirname('nodirs'))
    if path == '':
        return

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            return
        else:
            raise e


def search_by(cur, field, query, extent='whole', regexp=False, case_sensitive=False, frequent=False):
    '''Main search function.  Return list of ent_seqs.

    Field in ('kanji', 'reading', 'gloss').
    '''

    if regexp:
        operator = 'REGEXP ?'

        if extent == 'whole':
            query = '^' + query + '$'
        elif extent == 'word':
            query = r'\b' + query + r'\b'

    else:
        if extent == 'word':
            # we custom-implemented match() to whole-word search.
            #
            # it uses regexps internally though (but the user query is
            # escaped).
            operator = 'MATCH ?'

        else:
            # LIKE gives us case-insensitiveness implemented in the
            # database, so we usen it even for whole-field matching.
            #
            # "\" seems to be the least common character in EDICT.
            operator = r"LIKE ? ESCAPE '\'"

            # my editor doesn't like raw strings
            # query = query.replace(r'\', r'\\')
            query = query.replace('\\', '\\\\')

            query = query.replace('%', r'\%')
            query = query.replace('_', r'\_')

            if extent == 'partial':
                query = '%' + query + '%'

    if field == 'kanji':
        table = 'kanjis'
        join = 'NATURAL JOIN kanjis'
    elif field == 'reading':
        table = 'readings'
        join = 'NATURAL JOIN readings'
    elif field == 'gloss':
        table = 'glosses'
        join = 'NATURAL JOIN senses JOIN glosses ON senses.id = glosses.sense_id'

    where_extra = ''
    if frequent:
        where_extra += 'AND frequent = 1'

    cur.execute('''
SELECT ent_seq
FROM entries
  %s
WHERE %s.%s %s
%s
;'''
                % (join, table, field, operator, where_extra),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res


def guess_search(cur, conditions):
    '''Try many searches; stop at first successful.

    conditions -- list of dictionaries.

    Each dictionary in *conditions is a set of keyword arguments for
    search_by() (including the mandatory arguments!).

    guess_search will try all in order, and choose the first one with
    >0 results.

    Return value: 2-tuple (condition, entries) where:
     - condition is the chosen search condition
     - entries is a list of entries (see search_by() )
    '''

    for condition in conditions:
        res = search_by(cur, **condition)
        if len(res) > 0:
            return (condition, res)
    return (None, [])

def matched_regexp(search_params):
    '''Return a regexp that reflects what the search_params matched.

    Used to color the result, with the params returned by guess_search().
    '''

    # TODO: there's some duplication between this logic and search_by()

    reg = search_params['query']
    if not search_params['regexp']:
        reg = re.escape(reg)

    if search_params['extent'] == 'whole':
        reg = '^' + reg + '$'
    elif search_params['extent'] == 'word':
        reg = r'\b' + reg + r'\b'

    if search_params['case_sensitive']:
        reg = get_regexp(reg, 0)
    else:
        reg = get_regexp(reg, re.I)

    return reg

def short_expansion(cur, abbrev):
    cur.execute(''' SELECT short_expansion FROM abbreviations WHERE abbrev = ? ;''', [abbrev])
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return None

def abbrev_line(cur, abbrev):
    exp = short_expansion(cur, abbrev)
    abbrev = fmt(abbrev, 'subdue')
    return "%s\t%s" % (abbrev, exp)

def abbrevs_table(cur):
    cur.execute('''
    SELECT abbrev
    FROM abbreviations
    ORDER BY abbrev
    ;''')

    abbrevs=[]
    for row in cur.fetchall():
        abbrevs.append(row[0])
    return "\n".join([abbrev_line(cur, abbrev) for abbrev in abbrevs])

# credits: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def version(cur):
    import argparse
    import romkan
    # import termcolor # no version
    import platform

    try:
        import psutil
        psutil_version = psutil.__version__
    except ImportError:
        psutil_version = None

    cur.execute('''
    SELECT dbversion, jmdict_mtime
    FROM versions;
    ''')
    row = cur.fetchone()
    dbversion = row[0]
    jmdict_mtime = row[1]

    scripts = {}
    for s in ('gzip', 'rsync', 'nice', 'ionice'):
        path = which(s)
        if path:
            scripts[s] = fmt(path, 'parameter')
        else:
            scripts[s] = fmt(path, 'warning')

    return ('''
myougiden version %s , database v. %s
JMdict last modified %s
Python version %s (%s)

Libraries:
  romkan: %s
  argparse: %s
  psutil: %s

External programs:
  gzip: %s
  rsync: %s
  nice: %s
  ionice: %s
'''.strip() % (
    fmt(config['core']['version'], 'parameter'),
    fmt(dbversion, 'parameter'),
    fmt(jmdict_mtime, 'parameter'),
    fmt(platform.python_version(), 'parameter'),
    fmt(platform.platform(), 'parameter'),

    fmt(romkan.__version__, 'parameter'),
    # fmt(termcolor.__version__, 'parameter'),
    fmt(argparse.__version__, 'parameter'),
    fmt(psutil_version, 'parameter'),

    scripts['gzip'],
    scripts['rsync'],
    scripts['nice'],
    scripts['ionice'],
    ))
