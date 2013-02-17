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
def get_regex(pattern):
    if pattern in regexp_store.keys():
        return regexp_store[pattern]
    else:
        comp = re.compile(pattern, re.I)
        regexp_store[pattern] = comp
        return comp

def regexp(pattern, field):
    # print(pattern, field)
    reg = get_regex(pattern)
    return reg.search(field) is not None

def opendb():
    con = sql.connect(PATHS['database'])
    con.create_function('regexp', 2, regexp)
    cur = con.cursor()
    return con, cur

def format_entry(kanjis, readings, senses):

    return '%s\t%s\t%s' % (
        '；'.join(kanjis),
        '；'.join(readings),
        ';'.join(senses)
        )

def fetch_and_format_entries(cur, entries):
    lines = []
    for entry in entries:
        kanjis = []
        readings = []
        senses = []

        cur.execute('SELECT kanji FROM kanjis WHERE ent_seq = ?;', [entry])
        for row in cur.fetchall():
            kanjis.append(row[0])

        cur.execute('SELECT reading FROM readings WHERE ent_seq = ?;', [entry])
        for row in cur.fetchall():
            readings.append(row[0])

        cur.execute('SELECT sense FROM senses WHERE ent_seq = ?;', [entry])
        for row in cur.fetchall():
            senses.append(row[0])

        lines.append(format_entry(kanjis, readings, senses))
    return lines

def search_by(cur, field, query, partial=False, word=False, regexp=False):
    if field == 'kanji':
        table = 'kanjis'
    elif field == 'reading':
        table = 'readings'
    elif field == 'sense':
        table = 'senses'

    if regexp:
        operator = 'REGEXP'
    else:
        operator = 'LIKE'

    if regexp:
        if word:
            query = '\\b' + query + '\\b'
        elif not partial:
            query = '^' + query + '$'
    else:
        if word:
            pass # TODO
        elif partial:
            query = '%' + query + '%'

    cur.execute('''
SELECT ent_seq
FROM entries
  NATURAL INNER JOIN %s
WHERE %s.%s %s ?
;'''
                % (table, table, field, operator),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res

if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser()

    ap.add_argument('-k', '--by-kanji', action='store_const', dest='field', const='kanji', default='guess',
                    help="Search entry with kanji field matching query")

    ap.add_argument('-r', '--by-reading', action='store_const', dest='field', const='reading',
                    help="Search entry with reading field (in kana) matching query")

    ap.add_argument('-s', '--by-sense', action='store_const', dest='field', const='sense',
                    help="Search entry with sense field (English translation) matching query")


    ap.add_argument('-p', '--partial', action='store_true',
                    help="Search partial matches")

    ap.add_argument('-w', '--word', action='store_true',
                    help="Search partial matches, but only if query matches a whole word (FIXME: currently requires -x)")

    ap.add_argument('-x', '--regexp', action='store_true',
                    help="Regular expression search")

    ap.add_argument('query')

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


    con, cur = opendb()

    if args.field != 'guess':
        entries = search_by(cur, args.field, args.query,
                            partial=args.partial,
                            word=args.word,
                            regexp=args.regexp)
    else:
        entries = search_by(cur, 'kanji', args.query,
                            partial=args.partial,
                            word=args.word,
                            regexp=args.regexp)
        if len(entries) == 0:
            entries = search_by(cur, 'reading', args.query,
                                partial=args.partial,
                                word=args.word,
                                regexp=args.regexp)
            if len(entries) == 0:
                entries = search_by(cur, 'sense', args.query,
                                    partial=args.partial,
                                    word=args.word,
                                    regexp=args.regexp)

    for line in fetch_and_format_entries(cur, entries):
        print(line)
