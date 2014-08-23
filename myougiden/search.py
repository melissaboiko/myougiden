import re
from myougiden import texttools as tt

def search_by(cur, field, query, extent='whole', regexp=False, case_sensitive=False, frequent=False):
    '''Main search function.  Return list of ent_seqs.

    Field in ('kanji', 'reading', 'gloss').
    Extent in ('whole', 'beginning', 'word', 'partial').
    '''

    if (field == 'gloss' and case_sensitive) or extent in ('whole', 'partial'):
        fts=False
    else:
        fts=True

    if fts:
        if field == 'kanji':
            table = 'kanjis_fts'
        elif field == 'reading':
            table = 'readings_fts'
        elif field == 'gloss':
            table = 'glosses_fts'
    else:
        if field == 'kanji':
            table = 'kanjis'
        elif field == 'reading':
            table = 'readings'
        elif field == 'gloss':
            table = 'glosses'

    where_extra = ''

    if regexp:
        # case sensitivity set for operator in opendb()
        operator = 'REGEXP ?'

        if extent == 'whole':
            query = '^' + query + '$'
        elif extent == 'beginning':
            query = '^' + query
        elif extent == 'word':
            query = r'\b' + query + r'\b'

    else:
        if fts:
            operator = 'MATCH ?'
            if extent == 'beginning':
                query = query + '*'

        else:

            if extent == 'whole':
                operator = '= ?'
                query = query.replace('\\', '\\\\')
                if case_sensitive and field == 'gloss':
                    where_extra = 'COLLATE BINARY';

            else:
                # extent = 'partial

                # "\" seems to be the least common character in EDICT.
                operator = r"LIKE ? ESCAPE '\'"

                # my editor doesn't like raw strings
                # query = query.replace(r'\', r'\\')
                query = query.replace('\\', '\\\\')

                query = query.replace('%', r'\%')
                query = query.replace('_', r'\_')

                query = '%' + query + '%'

    if frequent:
        where_extra += ' AND %s.frequent = 1' % table

    print('''
SELECT DISTINCT ent_seq
FROM %s
WHERE %s %s %s
;'''
                % (table, field, operator, where_extra),
                [query])

    cur.execute('''
SELECT DISTINCT ent_seq
FROM %s
WHERE %s %s %s
;'''
                % (table, field, operator, where_extra),
                [query])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res


def guess(cur, conditions):
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
    elif search_params['extent'] == 'beginning':
        reg = '^' + reg
    elif search_params['extent'] == 'word':
        reg = r'\b' + reg + r'\b'

    if search_params['case_sensitive']:
        reg = tt.get_regexp(reg, 0)
    else:
        reg = tt.get_regexp(reg, re.I)

    return reg


