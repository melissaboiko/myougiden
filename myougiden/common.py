import errno
import sys
import os
import re
import romkan
import configparser

from myougiden import *
from myougiden.texttools import *
from myougiden.color import fmt, colorize_data

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


class Sense():
    '''Attributes:
    - glosses: a list of glosses.
    - pos: part-of-speech.
    - misc: other info, abbreviated.
    - dial: dialect.
    - s_inf: long case-by-case remarks.
    - id: database ID.
    '''

    def __init__(self,
                 id=None,
                 pos=None,
                 misc=None,
                 dial=None,
                 s_inf=None,
                 glosses=None):
        self.id = id
        self.pos = pos
        self.misc = misc
        self.dial = dial
        self.s_inf = s_inf
        self.glosses = glosses or list()

    def tagstr(self):
        '''Return a string with all information tags.'''

        tagstr = ''
        tags = []
        for attr in ('pos', 'misc', 'dial'):
            tag = getattr(self, attr)
            if tag:
                tags.append(tag)
        if len(tags) > 0:
            tagstr += '[%s]' % (','.join(tags))

        if self.s_inf:
            if len(tagstr) > 0:
                tagstr += ' '
            tagstr += '[%s]' % self.s_inf

        return fmt(tagstr, 'subdue')


# this thing really needs to be better thought of
def format_entry_tsv(kanjis, readings, senses, is_frequent,
                     search_params,
                     romajifn=None):
    # as of 2012-02-21, no reading or kanji field uses full-width semicolon
    sep_full = '；'

    # as of 2012-02-21, only one entry uses '|' .
    # and it's "C|NET", which should be "CNET" anyway.
    sep_half = '|'

    # escape separator
    for sense in senses:
        for idx, gloss in enumerate(sense.glosses):
            # I am unreasonably proud of this solution.
            sense.glosses[idx] = sense.glosses[idx].replace(sep_half, '¦')

    if is_frequent:
        freqmark = '(P)'

    sep_full = fmt(sep_full, 'subdue')
    sep_half = fmt(sep_half, 'subdue')
    if is_frequent:
        freqmark = fmt(freqmark, 'highlight')
    kanjis, readings, senses = colorize_data(kanjis, readings, senses, search_params)

    if romajifn:
        readings = [romajifn(r) for r in readings]

    s = ''

    s += "%s\t%s" % (sep_full.join(readings), sep_full.join(kanjis))
    for sense in senses:
        tagstr = sense.tagstr()
        if tagstr: tagstr += ' '

        s += "\t%s%s" % (tagstr, sep_half.join(sense.glosses))

    if is_frequent:
        s += ' '  + freqmark

    return s

def format_entry_human(kanjis, readings, senses, is_frequent,
                       search_params,
                       romajifn=None):
    sep_full = '；'
    sep_half = '; '

    if is_frequent:
        freqmark = '※'

    sep_full = fmt(sep_full, 'subdue')
    sep_half = fmt(sep_half, 'subdue')

    if is_frequent:
        freqmark = fmt(freqmark, 'highlight')
    kanjis, readings, senses = colorize_data(kanjis, readings, senses, search_params)

    if romajifn:
        readings = [romajifn(r) for r in readings]

    s = ''

    if is_frequent:
        s += freqmark + ' ' + sep_full.join(readings)
    else:
        s += sep_full.join(readings)

    if len(kanjis) > 0:
        s += "\n"
        s += sep_full.join(kanjis)

    for sensenum, sense in enumerate(senses, start=1):
        sn = str(sensenum) + '.'
        sn = fmt(sn, 'misc')

        tagstr = sense.tagstr()
        if tagstr: tagstr += ' '

        s += "\n%s %s%s" % (sn, tagstr, sep_half.join(sense.glosses))

    return s


def fetch_entry(cur, ent_seq):
    '''Return tuple of (kanjis, readings, senses, is_frequent).'''

    kanjis = [] # list of strings
    readings = [] # list of strings
    senses = [] # list of Sense objects

    cur.execute('SELECT frequent FROM entries WHERE ent_seq = ?;', [ent_seq])
    if cur.fetchone()[0] == 1:
        is_frequent = True
    else:
        is_frequent = False

    cur.execute('SELECT kanji FROM kanjis WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        kanjis.append(row[0])

    cur.execute('SELECT reading FROM readings WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        readings.append(row[0])

    senses = []
    cur.execute(
        'SELECT id, pos, misc, dial, s_inf FROM senses WHERE ent_seq = ?;',
        [ent_seq]
    )
    for row in cur.fetchall():
        sense = Sense(id=row[0],
                      pos=row[1],
                      misc=row[2],
                      dial=row[3],
                      s_inf=row[4])

        cur.execute('SELECT gloss FROM glosses WHERE sense_id = ?;', [sense.id])
        for row in cur.fetchall():
            sense.glosses.append(row[0])

        senses.append(sense)

    return (kanjis, readings, senses, is_frequent)

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
