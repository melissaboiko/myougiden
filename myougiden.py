#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import gzip
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
        ';'.join(senses)
        )

def format_entry_human(kanjis, readings, senses):
    s = ''

    s += '；'.join(readings)

    if len(kanjis) > 0:
        s += "\n"
        s += '；'.join(kanjis)

    # perhaps use a gloss table after all...
    i=1
    for sense in senses:
        s += "\n  %d. %s" % (i, sense)
        i += 1

    return s

def fetch_entry(cur, ent_seq):
    '''Return tuple of lists (kanjis, readings, senses).'''

    kanjis = []
    readings = []
    senses = []

    cur.execute('SELECT kanji FROM kanjis WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        kanjis.append(row[0])

    cur.execute('SELECT reading FROM readings WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        readings.append(row[0])

    cur.execute('SELECT sense FROM senses WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        senses.append(row[0])

    return (kanjis, readings, senses)


def search_by(cur, field, query, partial=False, word=False, regexp=False, case_sensitive=False):
    '''Main search function.  Return list of ent_seqs.

    Field in ('kanji', 'reading', 'sense').
    '''


    if field == 'kanji':
        table = 'kanjis'
    elif field == 'reading':
        table = 'readings'
    elif field == 'sense':
        table = 'senses'

    if regexp:
        operator = 'REGEXP ?'
        if word:
            query = r'\b' + query + r'\b'
        elif not partial:
            query = '^' + query + '$'

    else:
        if word:
            operator = 'MATCH ?'
        else:
            operator = r"LIKE ? escape '\'"

            # my editor doesn't like raw strings
            # query = query.replace(r'\', r'\\')
            query = query.replace('\\', '\\\\')

            query = query.replace('%', r'\%')
            query = query.replace('_', r'\_')


        if partial:
            query = '%' + query + '%'

    cur.execute('''
SELECT ent_seq
FROM entries
  NATURAL INNER JOIN %s
WHERE %s.%s %s
;'''
                % (table, table, field, operator),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res

def guess_search(cur, conditions):
    '''Try many searches.

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


if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    ag = ap.add_argument_group('Type of query',
                               '''What to look for.  If not provided, the program will attempt to guess
the query type.''')
    ag.add_argument('-k', '--by-kanji', action='store_const', dest='field', const='kanji', default='guess',
                    help='''Return entries matching query on kanji.''')

    ag.add_argument('-r', '--by-reading', action='store_const', dest='field', const='reading',
                    help='''Return entries matching query on reading (in kana).''')

    ag.add_argument('-s', '--by-sense', action='store_const', dest='field', const='sense',
                    help='''Return entries matching query on sense (English
translation).''')


    ag = ap.add_argument_group('Query options')
    ag.add_argument('--case-sensitive', '--sensitive', action='store_true',
                    help='''Case-sensitive search (distinguish uppercase from
lowercase). Default: Insensitive, unless there's an
uppercase letter in query.''')

    ag.add_argument('-p', '--partial', action='store_true',
                    help="Search partial matches.")

    ag.add_argument('-w', '--word', action='store_true',
                    help='''Search partial matches, but only if query matches a
whole word (FIXME: currently requires -x).''')

    ag.add_argument('-x', '--regexp', action='store_true',
                    help="Regular expression search.")

    ag = ap.add_argument_group('Output control')
    ag.add_argument('--output-mode', default='auto', choices=('human', 'tab', 'auto'),
                    help="""Output mode; one of:
 - 'human': Multiline human-readable output.
 - 'tab': One-line tab-separated.
 - 'auto' (default): Human if output is to terminal,
    tab if writing to pipe or file.""")

    ag.add_argument('-t', '--tsv', '--tab', action='store_const', const='tab', dest='output_mode',
                    help="Equivalent to --output=mode=tab")

    ap.add_argument('query', help='Text to look for.')

    # ap.add_argument('--db-compress',
    #                 action='store_true',
    #                 help='Compress myougiden database.  Uses less disk space, but queries are slower.')
    # ap.add_argument('--db-uncompress',
    #                 action='store_true',
    #                 help='Uncompress myougiden database.  Uses more disk space, but queries are faster.')

    args = ap.parse_args()


    # if args.db_compress:
    #     subprocess.call(['gzip', PATHS['database']])
    # elif args.db_uncompress:
    #     subprocess.call(['gzip', '-d', PATHS['database']])

    if args.output_mode == 'auto':
        if sys.stdout.isatty():
            args.output_mode = 'human'
        else:
            args.output_mode = 'tab'

    if not args.case_sensitive:
        if  re.search("[A-Z]", args.query):
            args.case_sensitive = True

    con, cur = opendb(case_sensitive=args.case_sensitive)

    search_args = vars(args).copy() # turn Namespace to dict
    # and delete all command-line options which aren't search_by()
    # options

    del search_args['output_mode']

    if args.field != 'guess':
        entries = search_by(cur, **search_args)
    else:
        conditions = []

        search_args['field'] = 'kanji'
        conditions.append(search_args.copy())
        search_args['field'] = 'reading'
        conditions.append(search_args.copy())
        search_args['field'] = 'sense'
        conditions.append(search_args.copy())

        entries = guess_search(cur, conditions)

    if args.output_mode == 'human':
        rows = [fetch_entry(cur, ent_seq) for ent_seq in entries]
        print("\n\n".join([format_entry_human(*row) for row in rows]))

    elif args.output_mode == 'tab':
        for row in [fetch_entry(cur, ent_seq) for ent_seq in entries]:
            print(format_entry_tsv(*row))
