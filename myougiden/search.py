import re
import romkan
from myougiden import common
from myougiden import database
from myougiden import texttools as tt
from copy import deepcopy

class SearchConditions():
    '''A set of conditions to query the dictionary.

    Argument to search_by().

    Sortable.  The esoteric sorting rules implement myougiden's automagic guess
    search.'''

    def __init__(self,
                 cmdline_args,
                 query,
                 regexp,
                 field,
                 extent,
                ):
        self.regexp = regexp
        self.field = field
        self.extent = extent

        self.query = query
        self.query_s = ' '.join(query)
        self.case_sensitive = cmdline_args.case_sensitive
        self.frequent = cmdline_args.frequent

        self.args = cmdline_args


    def extent_sort_key(self):
        return ['whole','word','beginning','partial'].index(self.extent)

    def field_sort_key(self):
        if tt.is_kana(self.args.query_s):
            return ['reading', 'kanji'].index(self.field)

        elif tt.is_latin(self.args.query_s):
            if self.args.field == 'reading':
                # try it converted to kana first
                return ['reading', 'gloss', 'kanji'].index(self.field)
            else:
                # try to interpret as gloss first
                return ['gloss', 'reading', 'kanji'].index(self.field)
        else:
            # doesn't look like kana or latin, probably kanji but who knows
            return ['kanji', 'reading', 'gloss'].index(self.field)


    def sort_key(self):
        if self.regexp == True:
            regexp_key = 2
        else:
            regexp_key = 1

        field_key = self.field_sort_key()
        extent_key = self.extent_sort_key()

        # basically we try all extents before trying other fields.
        # however, 'partial' extents are a last resort, so they are only tried
        # separatedly, after trying all fields.
        if self.extent == 'partial':
            partial_key = 2
        else:
            partial_key = 1

        return [regexp_key, partial_key, field_key, extent_key]

    def __repr__(self):
        return("'%s': regexp %s, field %s, extent %s\n sort key: %s" %
              (list(self.query), self.regexp, self.field, self.extent,
               self.sort_key()))

def generate_search_conditions(args):
    '''args = command-line argument dict (argparse object)'''

    if args.regexp:
        regexp_flags = (True,)
    elif tt.has_regexp_special(args.query_s):
        regexp_flags = (False, True)
    else:
        regexp_flags = (False,)

    if args.field != 'auto':
        fields = (args.field,)
    else:
        if tt.is_kana(args.query_s):
            fields = ('kanji', 'reading')
        else:
            fields = ('kanji', 'reading', 'gloss')

    if args.extent != 'auto':
        extents = (args.extent,)
    else:
        extents = ('whole', 'word', 'beginning', 'partial')

    conditions = []

    for regexp in regexp_flags:
        for field in fields:
            for extent in extents:

                if field == 'gloss' and extent == 'beginning' and args.extent == 'auto':
                    # when we search for e.g. 'man' in auto guesses, we
                    # typically don't want 'manatee' but not 'humanity'
                    continue

                elif field in ('kanji', 'reading') and extent == 'word':
                    if args.extent == 'auto':
                        # useless combination generated, skip
                        continue
                    else:
                        # useless combination requested, adjust
                        extent = 'whole'

                if field == 'reading' and tt.is_latin(args.query_s):
                    # 'reading' field auto-convert romaji to kana. as of this
                    # writing, JMdict has no romaji in readingfields.
                    queries = ([romkan.to_hiragana(s) for s in args.query],
                               [romkan.to_katakana(s) for s in args.query])

                    # romkan will convert ASCII hyphen-minus to CJKV long 'ー'
                    # we back-convert it in start position, to preserve FTS
                    # operator '-'.
                    def fix_hyphen(s):
                        if len(s) > 1 and s[0] == 'ー':
                            s = '-' + s[1:]
                        return s

                    queries = [[fix_hyphen(s) for s in query]
                               for query in queries]
                else:
                    queries = (args.query,)
                # TODO: add wide-char

                for query in queries:
                    conditions.append(SearchConditions(args, query, regexp, field, extent))

    return conditions

def search_by(cur, cond):
    '''Main search function.  Take a SearchCondition object, return list of ent_seqs.
    '''

    if ((cond.field == 'gloss' and cond.case_sensitive)
        or cond.extent in ('whole', 'partial')):
        fts=False
        query_s = cond.query_s[:]
    else:
        fts=True
        query_prep = []
        for cmdline_arg in cond.query:
            # unify Japanese spaces, newlines etc. to a single space
            re.sub('\\s+', ' ', cmdline_arg)

            # if the user called
            #
            #    myougiden 'full phrase'
            #
            # or
            #    myougiden "full phrase"
            #
            # we'll get a single argv with spaces in it.  in this case we
            # translate the argv to the string
            #
            #    "full phrase"
            #
            # (including the double quotes), which is what sqlite FTS looks
            # for.
            if ' ' in cmdline_arg:
                cmdline_arg = '"' + cmdline_arg + '"'

            if cond.extent == 'beginning':
                cmdline_arg += '*'

            query_prep.append(cmdline_arg)

        query_s = ' '.join(query_prep)

    if fts:
        if cond.field == 'kanji':
            table = 'kanjis_fts'
        elif cond.field == 'reading':
            table = 'readings_fts'
        elif cond.field == 'gloss':
            table = 'glosses_fts'
    else:
        if cond.field == 'kanji':
            table = 'kanjis'
        elif cond.field == 'reading':
            table = 'readings'
        elif cond.field == 'gloss':
            table = 'glosses'

    where_extra = ''

    if cond.regexp or (not fts and cond.extent == 'word'):
        # case sensitivity set for operator in opendb()
        operator = 'REGEXP ?'

        if cond.extent == 'whole':
            query_s = '^' + query_s + '$'
        elif cond.extent == 'beginning':
            query_s = '^' + query_s
        elif cond.extent == 'word':
            query_s = r'\b' + query_s + r'\b'

    else:
        if fts:
            operator = 'MATCH ?'

        else:

            if cond.extent == 'whole':
                operator = '= ?'
                query_s = query_s.replace('\\', '\\\\')
                if cond.case_sensitive and cond.field == 'gloss':
                    where_extra = 'COLLATE BINARY';

            else:
                # extent = 'partial

                # "\" seems to be the least common character in EDICT.
                operator = r"LIKE ? ESCAPE '\'"

                # my editor doesn't like raw strings
                # query_s = query_s.replace(r'\', r'\\')
                query_s = query_s.replace('\\', '\\\\')

                query_s = query_s.replace('%', r'\%')
                query_s = query_s.replace('_', r'\_')

                query_s = '%' + query_s + '%'

    if cond.frequent:
        where_extra += ' AND %s.frequent = 1' % table


    database.execute(cur, '''
SELECT DISTINCT ent_seq
FROM %s
WHERE %s %s %s
;'''
                % (table, cond.field, operator, where_extra),
                [query_s])

    res = []
    for row in cur.fetchall():
        res.append(row[0])
    return res


def guess(cur, conditions):
    '''Try many searches; stop at first successful.

    conditions -- list of SearchConditions.

    guess() will try all in sort order, and choose the first one with
    >0 results.

    Return value: 2-tuple (condition, entries) where:
     - condition is the chosen SearchConditions object
     - entries is a list of entries (see search_by() )
    '''

    conditions.sort(key=lambda cond: cond.sort_key())
    if common.debug:
        import pprint; pprint.pprint(conditions)
    for condition in conditions:
        res = search_by(cur, condition)
        if len(res) > 0:
            return (condition, res)
    return (None, [])

def matched_regexp(conds):
    '''Return a regexp that reflects what the SearchConditions matched.

    Used to color the result, with the params returned by guess().
    '''

    # TODO: there's some duplication between this logic and search_by()
    # TODO: support word search

    reg = conds.query_s
    if not conds.regexp:
        reg = re.escape(reg)

    if conds.extent == 'whole':
        reg = '^' + reg + '$'
    elif conds.extent == 'beginning':
        reg = '^' + reg
    elif conds.extent == 'word':
        reg = r'\b' + reg + r'\b'

    if conds.case_sensitive:
        reg = tt.get_regexp(reg, 0)
    else:
        reg = tt.get_regexp(reg, re.I)

    return reg


