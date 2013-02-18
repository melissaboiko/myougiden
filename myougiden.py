#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import gzip
from pprint import pprint
import sqlite3 as sql
# import subprocess

PATHS = {}
PATHS['sharedir'] = '.'
PATHS['database'] = os.path.join(PATHS['sharedir'], 'jmdict.sqlite')
PATHS['jmdict_url'] = 'http://ftp.monash.edu.au/pub/nihongo/JMdict_e.gz'

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


def has_alpha(string):
    return re.search('[a-z]', string, re.I) is not None


if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    ag = ap.add_argument_group('Type of query',
                               '''What to look for.  If not provided, the program will attempt to guess
the query type.''')
    ag.add_argument('-k', '--kanji', action='store_const', dest='field', const='kanji', default='auto',
                    help='''Return entries matching query on kanji.''')

    ag.add_argument('-r', '--reading', action='store_const', dest='field', const='reading',
                    help='''Return entries matching query on reading (in kana).''')

    ag.add_argument('-g', '--gloss', action='store_const', dest='field', const='gloss',
                    help='''Return entries matching query on glosses (English
translations/meaning).''')


    ag = ap.add_argument_group('Query options')
    ag.add_argument('--case-sensitive', '--sensitive', action='store_true',
                    help='''Case-sensitive search (distinguish uppercase from
lowercase). Default: Insensitive, unless there's an
uppercase letter in query.''')

    ag.add_argument('-x', '--regexp', action='store_true',
                    help="Regular expression search.")

    ag.add_argument('-e', '--extent', default='auto',
                    choices=('whole', 'word', 'partial', 'auto'),
                    help='''How much of the field should the query match:
 - whole: Query must match the entire field.
 - word: Query must match whole word (at present
   only works for English; treated as 'whole' for
   kanji or reading fields.)
 - partial: Query may match anything.
 - auto (default): Try all three, and return
   first that matches something.''')

    ag.add_argument('-w', '--whole', action='store_const', const='whole', dest='extent',
                    help='''Equivalent to --extent=whole.''')

    ag.add_argument('--word', action='store_const', const='word', dest='extent',
                    help='''Equivalent to --extent=word.''')

    ag.add_argument('-p', '--partial', action='store_const', const='partial', dest='extent',
                    help='Equivalent to --extent=partial.')



    ag = ap.add_argument_group('Output control')
    ag.add_argument('--output-mode', default='auto', choices=('human', 'tab', 'auto'),
                    help='''Output mode; one of:
 - human: Multiline human-readable output.
 - tab: One-line tab-separated.
 - auto (default): Human if output is to terminal,
    tab if writing to pipe or file.''')

    ag.add_argument('-t', '--tsv', '--tab', action='store_const', const='tab', dest='output_mode',
                    help="Equivalent to --output=mode=tab")

    ap.add_argument('query', help='Text to look for.', metavar='QUERY')


    args = ap.parse_args()


    # first, handle various guesswork
    if args.output_mode == 'auto':
        if sys.stdout.isatty():
            args.output_mode = 'human'
        else:
            args.output_mode = 'tab'


    if not args.case_sensitive:
        if  re.search("[A-Z]", args.query):
            args.case_sensitive = True


    # 'word' doesn't work for Jap. anyway, and 'whole' is much faster.
    if args.extent == 'word' and args.field in ('kanji', 'reading'):
        args.extent = 'whole'


    # now handle search guesses.

    # first, we need a dictionary of options with only keys understood
    # by search_by().
    search_args = vars(args).copy() # turn Namespace to dict
    del search_args['output_mode']

    # we'll iterate over all required 'field' and 'extent' conditions.
    #
    # for code clarity, we always use a list of search conditions,
    # even if the size of the list is 1.

    if args.field != 'auto':
        fields = (args.field,)
    else:
        if has_alpha(args.query):
            # alphabet probably means English; smarter order to
            # search.
            fields = ('gloss', 'kanji', 'reading')
        else:
            # TODO: if string is kana-only, search reading first.
            fields = ('kanji', 'reading', 'gloss')

    if args.extent != 'auto':
        extents = (args.extent,)
    else:
        extents = ('whole', 'word', 'partial')


    conditions = []
    for extent in extents:
        for field in fields:

            # the useless combination; we'll avoid it to avoid wasting
            # time.
            if extent == 'word' and field != 'gloss':

                if args.extent == 'auto':
                    # we're trying all possibilities, so we can just
                    # skip this one.  other extents were/will be tried
                    # elsewhen in the loop.
                    continue
                else:
                    # not trying all possibilities; this is our only
                    # pass in this field, so let's adjust it.
                    sa = search_args.copy()
                    sa['extent'] = 'whole'
            else:
                # simple case.
                sa = search_args.copy()
                sa['extent'] = extent

            sa['field'] = field

            conditions.append(sa)

    # pprint(conditions)
    con, cur = opendb(case_sensitive=args.case_sensitive)
    entries = guess_search(cur, conditions)

    if len(entries) > 0:
        if args.output_mode == 'human':
            rows = [fetch_entry(cur, ent_seq) for ent_seq in entries]
            print("\n\n".join([format_entry_human(*row) for row in rows]))

        elif args.output_mode == 'tab':
            for row in [fetch_entry(cur, ent_seq) for ent_seq in entries]:
                print(format_entry_tsv(*row))
    else:
        sys.exit(1)
