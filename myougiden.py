import sys
import os
import re
import sqlite3 as sql

PATHS = {}

PATHS['pkgprefix'] = os.path.realpath(os.path.dirname(__file__))
PATHS['vardir'] = os.path.join(PATHS['pkgprefix'], 'var')
PATHS['database'] = os.path.join(PATHS['vardir'], 'jmdict.sqlite')
PATHS['jmdict_url'] = 'http://ftp.monash.edu.au/pub/nihongo/JMdict_e.gz'

# extracted from edict "reading" fields. TODO: cross-check with Unicode
edict_kana='・？ヽヾゝゞー〜ぁあぃいうぇえおかがきぎくぐけげこごさざしじすずせぜそぞただちっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわゐゑをんァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヶ'
edict_kana_regexp=re.compile("^[%s]*$" % edict_kana)
def is_kana(string):
    return re.match(edict_kana_regexp, string) is not None

def has_alpha(string):
    return re.search('[a-z]', string, re.I) is not None

regexp_store = {}
def get_regex(pattern, flags):
    '''Return a compiled regexp from persistent store; make one if needed.

    We use this helper function so that the SQL hooks don't have to
    compile the same regexp at every query.

    Flags are not part of the hash; i.e. this function doesn't work
    for the same pattern with different flags.
    '''

    if pattern in regexp_store.keys():
        return regexp_store[pattern]
    else:
        comp = re.compile(pattern, re.U | flags)
        regexp_store[pattern] = comp
        return comp


def regexp_sensitive(pattern, field):
    '''SQL hook function for case-sensitive regexp matching.'''
    reg = get_regex(pattern, 0)
    return reg.search(field) is not None

def regexp_insensitive(pattern, field):
    '''SQL hook function for case-insensitive regexp matching.'''
    reg = get_regex(pattern, re.I)
    return reg.search(field) is not None

def match_word_sensitive(word, field):
    '''SQL hook function for whole-word, case-sensitive, non-regexp matching.'''
    reg = get_regex(r'\b' + re.escape(word) + r'\b', 0)
    return reg.search(field) is not None

def match_word_insensitive(word, field):
    '''SQL hook function for whole-word, case-sensitive, non-regexp matching.'''
    reg = get_regex(r'\b' + re.escape(word) + r'\b', re.I)
    return reg.search(field) is not None


def opendb(case_sensitive=False):
    '''Open SQL database; returns (con, cur).'''

    con = sql.connect(PATHS['database'])
    cur = con.cursor()

    if case_sensitive:
        con.create_function('regexp', 2, regexp_sensitive)
        con.create_function('match', 2, match_word_sensitive)
        cur.execute('PRAGMA case_sensitive_like = 1;')
    else:
        con.create_function('regexp', 2, regexp_insensitive)
        con.create_function('match', 2, match_word_insensitive)
        cur.execute('PRAGMA case_sensitive_like = 0;')


    return con, cur

def format_entry_tsv(kanjis, readings, senses):
    return '%s\t%s\t%s' % (
        '；'.join(kanjis),
        '；'.join(readings),
        "\t".join(['; '.join(glosses_list) for glosses_list in senses])
        )

def format_entry_human(kanjis, readings, senses):
    s = ''

    s += '；'.join(readings)

    if len(kanjis) > 0:
        s += "\n"
        s += '；'.join(kanjis)

    # perhaps use a gloss table after all...
    i=1
    for glosses_list in senses:
        s += "\n  %d. %s" % (i, '; '.join(glosses_list))
        i += 1

    return s

def fetch_entry(cur, ent_seq):
    '''Return tuple of lists (kanjis, readings, senses).'''

    kanjis = []
    readings = []
    senses = [] # list of list of glosses

    cur.execute('SELECT kanji FROM kanjis WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        kanjis.append(row[0])

    cur.execute('SELECT reading FROM readings WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        readings.append(row[0])

    sense_ids = []
    cur.execute('SELECT id FROM senses WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        sense_ids.append(row[0])
    for sense_id in sense_ids:
        glosses = []

        cur.execute('SELECT gloss FROM glosses WHERE sense_id = ?;', [sense_id])
        for row in cur.fetchall():
            glosses.append(row[0])

        senses.append(glosses)

    return (kanjis, readings, senses)


def search_by(cur, field, query, extent='whole', regexp=False, case_sensitive=False):
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

    # print('SELECT ent_seq FROM entries %s WHERE %s.%s %s;'
    #       % (join, table, field, operator),
    #       query)

    cur.execute('''
SELECT ent_seq
FROM entries
  %s
WHERE %s.%s %s
;'''
                % (join, table, field, operator),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res


def guess_search(cur, conditions):
    '''Try many searches, return first successful.

    conditions -- list of dictionaries.

    Each dictionary in *conditions is a set of keyword arguments for
    search_by() (including the mandatory arguments!).

    guess_search will try all in order, and return the first one with
    >0 results.
    '''

    for condition in conditions:
        res = search_by(cur, **condition)
        if len(res) > 0:
            return res
    return []


