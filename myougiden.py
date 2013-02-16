#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import gzip
import sqlite3 as sql
import subprocess
# import lxml.etree as ET
import xml.etree.cElementTree as ET


paths = {}
paths['sharedir'] = '.'
paths['database'] = os.path.join(paths['sharedir'], 'jmdict.sqlite')


def opendb():
    con = sql.connect(paths['database'])
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

def search_by(cur, field, query, partial=False):
    if field == 'kanji':
        table = 'kanjis'
    elif field == 'reading':
        table = 'readings'
    elif field == 'sense':
        table = 'senses'

    if partial:
        query = '%' + query + '%'

    cur.execute('''
SELECT ent_seq
FROM entries
  NATURAL INNER JOIN %s
WHERE %s.%s LIKE ?
;'''
                % (table, table, field),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res

if __name__ == '__main__':
    import argparse

    ap = argparse.ArgumentParser()

    ap.add_argument('-k', '--by-kanji', metavar='QUERY',
                    help="Search entry with kanji field matching query")

    ap.add_argument('-p', '--partial', action='store_true',
                    help="Search partial matches")

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

    if args.by_kanji:
        entries = search_by(cur, 'kanji', args.by_kanji, partial=args.partial)
        for line in fetch_and_format_entries(cur, entries):
            print(line)
