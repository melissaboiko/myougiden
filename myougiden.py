#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import gzip
import sqlite3 as sql
import subprocess
# import lxml.etree as ET
import xml.etree.cElementTree as ET


paths = {}
paths['sharedir'] = '.'
paths['database'] = os.path.join(paths['sharedir'], 'jmdict.sqlite')

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
    con = sql.connect(paths['database'])
    con.create_function('regexp', 2, regexp)
    cur = con.cursor()
    return con, cur

def create_table(cur):
    # what about a custom collation function?

    # my version of sqlite3 doesn't seem to work with executemany()
    cur.execute('DROP TABLE IF EXISTS kanjis;')
    cur.execute('DROP TABLE IF EXISTS readings;')
    cur.execute('DROP TABLE IF EXISTS senses;')
    cur.execute('DROP TABLE IF EXISTS entries;')

    cur.execute('''
      CREATE TABLE 
      entries (
        ent_seq INTEGER PRIMARY KEY
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      kanjis (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kanji TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      readings (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE TABLE 
      senses (
        ent_seq INTEGER NOT NULL,
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sense TEXT NOT NULL,
        FOREIGN KEY (ent_seq) REFERENCES entries(ent_seq)
      );
    ''')

    cur.execute('''
      CREATE INDEX kanjis_ent_seq ON kanjis (ent_seq);
    ''')
    cur.execute('''
      CREATE INDEX readings_ent_seq ON readings (ent_seq);
    ''')
    cur.execute('''
      CREATE INDEX senses_ent_seq ON senses (ent_seq);
    ''')

    cur.execute('''
      CREATE INDEX kanjis_kanji ON kanjis (kanji);
    ''')
    cur.execute('''
      CREATE INDEX readings_reading ON readings (reading);
    ''')
    cur.execute('''
      CREATE INDEX senses_sense ON senses (sense);
    ''')


def insert_entry(cur, ent_seq, kanjis, readings, senses):
    cur.execute('INSERT INTO entries(ent_seq) VALUES (?);', [ent_seq])
    for kanji in kanjis:
        cur.execute('INSERT INTO kanjis(ent_seq, kanji) VALUES (?, ?);', [ent_seq, kanji])

    for reading in readings:
        cur.execute('INSERT INTO readings(ent_seq, reading) VALUES (?, ?);', [ent_seq, reading])

    for sense in senses:
        cur.execute('INSERT INTO senses(ent_seq, sense) VALUES (?, ?);', [ent_seq, sense])

def make_database(jmdict, sqlite):
    con, cur = opendb()
    tree = ET.parse(jmdict)

    create_table(cur)

    for entry in tree.findall('entry'):
        ent_seq = entry.find('ent_seq').text

        kanjis = []
        for kanji in entry.findall('k_ele'):
            kanjis.append(kanji.find('keb').text)

        readings = []
        for reading in entry.findall('r_ele'):
            readings.append(reading.find('reb').text)

        senses = []
        for sense in entry.findall('sense'):

            # for now I foresee no need for a separate glosses table
            glosses = []
            for gloss in sense.findall('gloss'):
                glosses.append(gloss.text)
            senses.append('; '.join(glosses))

        insert_entry(cur, ent_seq, kanjis, readings, senses)

    cur.close()
    con.commit()

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
                    help="Search partial matches, but only if query matches a whole word (FIXME: currently requires -x")

    ap.add_argument('-x', '--regexp', action='store_true',
                    help="Regular expression search")

    ap.add_argument('query')

    ap.add_argument('--db-update', nargs='?', const='./JMdict_e.gz', default=None, metavar='./JMdict_e.gz',
                    help="Update myougiden database with new JMdict_e.gz file.  Optional argument is path to JMdict.")

    # ap.add_argument('--db-compress',
    #                 action='store_true',
    #                 help='Compress myougiden database.  Uses less disk space, but queries are slower.')
    # ap.add_argument('--db-uncompress',
    #                 action='store_true',
    #                 help='Uncompress myougiden database.  Uses more disk space, but queries are faster.')

    args = ap.parse_args()

    if args.db_update:
        print("Updating database at %s from %s, please wait..." %
              (paths['database'], args.db_update))
        make_database(gzip.open(args.db_update, 'r'),
                      paths['database'])
        sys.exit(0)

    # if args.db_compress:
    #     subprocess.call(['gzip', paths['database']])
    # elif args.db_uncompress:
    #     subprocess.call(['gzip', '-d', paths['database']])


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
