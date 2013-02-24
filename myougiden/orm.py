from myougiden import config
from myougiden import search
from myougiden import color
from myougiden.color import fmt

class Entry():
    '''Equivalent to JMdict entry.'''
    def __init__(self,
                 entry_id=None, # our database-specific ID
                 ent_seq=None, # JMdict ID
                 kanjis=None, # list of Kanjis()
                 readings=None, # list of Readings()
                 senses=None, # list of Senses
                 frequent=False
                ):
        self.entry_id = entry_id
        self.ent_seq = ent_seq
        self.kanjis = kanjis or []
        self.readings = readings or []
        self.senses = senses or []
        self.frequent = frequent

    # TODO: more detailed
    def is_frequent(self):
        return self.frequent

    def colorize(self, search_params, romaji=False):
        '''Alter child elements to add color, including the matched search.'''

        if not color.use_color:
            return

        matchreg = search.matched_regexp(search_params)
        if search_params['field'] == 'reading':
            for reading in self.readings:
                reading.colorize(matchreg=matchreg, romaji=romaji)
            for kanjis in self.kanjis:
                kanjis.colorize()
            for sense in self.senses:
                sense.colorize()

        elif search_params['field'] == 'kanji':
            for reading in self.readings:
                reading.colorize()
            for kanjis in self.kanjis:
                kanjis.colorize(matchreg=matchreg)
            for sense in self.senses:
                sense.colorize()

        elif search_params['field'] == 'gloss':
            for reading in self.readings:
                reading.colorize()
            for kanjis in self.kanjis:
                kanjis.colorize()
            for sense in self.senses:
                sense.colorize(matchreg=matchreg)

    def process_restrictions(self, search_params):
        matchreg = search.matched_regexp(search_params)

        if search_params['field'] == 'reading':
            # if the user query only matched restricted readings,
            # we remove kanji not matching these restrictions.
            for r in self.readings:
                restrictions = []
                if matchreg.search(r.text):
                    # the search matches _at least_ this reading.
                    # but: it may match other readings
                    if not r.re_restr:
                        # it matched a search without restrictions,
                        # so we'll show all kanji.
                        break
                    else:
                        restrictions +=  r.re_restr

                if restrictions:
                    self.kanjis = [k for k in self.kanjis
                                   if k.text in restrictions]

                    # also remove any senses restricted to lost kanji
                    for s in self.senses[:]:
                        if s.stagk:
                            ks = [k.text for k in self.kanjis]
                            for stagk in s.stagk:
                                if stagk not in ks:
                                    self.senses.remove(s)

    # this thing really needs to be better thought of
    def format_tsv(self, search_params, romajifn=None):
        self.process_restrictions(search_params)
        self.colorize(search_params, romaji=romajifn)

        # as of 2012-02-22, no reading or kanji field uses full-width
        # semicolon.
        sep_full = fmt('；', 'subdue')

        # as of 2012-02-22, only one entry uses '|' .
        # and it's "c|net", which should be "CNET" anyway.
        sep_half = fmt('|', 'subdue')

        # escape separator
        for sense in self.senses:
            for idx, gloss in enumerate(sense.glosses):
                # I am unreasonably proud of this solution.
                sense.glosses[idx] = sense.glosses[idx].replace(sep_half, '¦')


        if romajifn:
            readings_str = sep_full.join([ romajifn(r.text) for r in self.readings])
        else:
            readings_str = sep_full.join([ r.text for r in self.readings])

        s = ''

        s += "%s\t%s" % (readings_str,
                         sep_full.join([k.text for k in self.kanjis]))

        for sense in self.senses:
            tagstr = sense.tagstr()
            if tagstr: tagstr += ' '

            s += "\t%s%s" % (tagstr, sep_half.join(sense.glosses))

        if self.is_frequent():
            s += ' ' + fmt('(P)', 'highlight')

        return s

    def format_human(self, search_params, romajifn=None):
        self.process_restrictions(search_params)
        self.colorize(search_params, romaji=romajifn)

        sep_full = fmt('；', 'subdue')
        sep_half = fmt('; ', 'subdue')


        s = ''

        if self.is_frequent():
            s += fmt('※', 'highlight') + ' '

        if romajifn:
            s += sep_full.join([romajifn(r.text) for r in self.readings])
        else:
            s += sep_full.join([r.text for r in self.readings])

        if len(self.kanjis) > 0:
            s += "\n"
            s += sep_full.join([k.text for k in self.kanjis])

        for sensenum, sense in enumerate(self.senses, start=1):
            sn = fmt('%d.' % sensenum, 'misc')

            tagstr = sense.tagstr()
            if tagstr: tagstr += ' '

            s += "\n%s %s%s" % (sn, tagstr, sep_half.join(sense.glosses))

        return s

class Kanji():
    '''Equivalent to JMdict <k_ele>.'''
    def __init__(self,
                 kanji_id=None,
                 text=None, # = keb
                 frequent=False,
                 inf=None):
        self.kanji_id = kanji_id
        self.text = text
        self.frequent = frequent
        self.inf = inf

    def colorize(self, matchreg=None):
        if matchreg:
            self.text = color.color_regexp(matchreg, self.text, 'kanji', 'matchjp')
        else:
            self.text = fmt(self.text, 'kanji')


class Reading():
    '''Equivalent to JMdict <r_ele>.'''
    def __init__(self,
                 reading_id=None,
                 text=None, # = reb
                 re_nokanji=False,
                 re_restr=None,
                 re_inf=None,
                 frequent=False,
                ):
        self.reading_id = reading_id
        self.text = text
        self.re_nokanji = re_nokanji
        self.re_restr = re_restr or []
        self.re_inf = re_inf
        self.frequent = frequent

    def colorize(self, matchreg=None, romaji=False):
        if matchreg:
            if romaji: style='match'
            else: style='matchjp'
            self.text = color.color_regexp(matchreg,
                                           self.text,
                                           base_style='reading',
                                           match_style=style)
        else:
            self.text = fmt(self.text, 'reading')

class Sense():
    '''Equivalent to JMdict <sense>.

    Attributes:
    - sense_id: database ID.
    - glosses: a list of glosses (as strings).
    - pos: part-of-speech.
    - misc: other info, abbreviated.
    - dial: dialect.
    - s_inf: long case-by-case remarks.
    - stagk: if non-empty, sense is restricted to these kanji.
    '''

    def __init__(self,
                 sense_id=None,
                 pos=None,
                 misc=None,
                 dial=None,
                 s_inf=None,
                 glosses=None,
                 stagk=None,
                ):
        self.sense_id = sense_id
        self.pos = pos
        self.misc = misc
        self.dial = dial
        self.s_inf = s_inf
        self.glosses = glosses or list()
        self.stagk = stagk or list()

    def tagstr(self):
        '''Return a string with all information tags.

        Automatic colors depending on myougiden.color.use_color .'''

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

        if len(tagstr) > 0:
            return fmt(tagstr, 'subdue')
        else:
            return ''

    def colorize(self, matchreg=None):
        '''Colorizes glosses if matchreg is not None.'''

        if matchreg:
            for idx, gloss in enumerate(self.glosses):
                self.glosses[idx] = color.color_regexp(matchreg, gloss)

def fetch_entry(cur, entry_id):
    '''Return Entry object..'''

    kanjis = []
    readings = []
    senses = []

    cur.execute('SELECT kanji_id, kanji FROM kanjis WHERE entry_id = ?;', [entry_id])
    for row in cur.fetchall():
        # TODO: k_inf, kpri
        kanjis.append(Kanji(
            kanji_id=row[0],
            text=row[1],
        ))

    cur.execute('''SELECT
                reading_id,
                reading,
                re_nokanji,
                frequent,
                re_inf
                FROM readings
                WHERE entry_id = ?;''', [entry_id])

    for row in cur.fetchall():
        # TODO: r_inf, rpri
        reading = Reading(
            reading_id=row[0],
            text=row[1],
            re_nokanji=row[2],
            frequent=row[3],
            re_inf=row[4],
        )

        cur.execute('''SELECT re_restr
                    FROM reading_restrictions
                    WHERE reading_id = ?;''',
                    [reading.reading_id])
        for row in cur.fetchall():
            reading.re_restr.append(row[0])

        readings.append(reading)


    senses = []
    cur.execute(
        'SELECT sense_id, pos, misc, dial, s_inf FROM senses WHERE entry_id = ?;',
        [entry_id]
    )
    for row in cur.fetchall():
        sense = Sense(sense_id=row[0],
                      pos=row[1],
                      misc=row[2],
                      dial=row[3],
                      s_inf=row[4])

        cur.execute('''
                    SELECT stagk
                    FROM sense_kanji_restrictions
                    WHERE sense_id = ?;
                    ''', [sense.sense_id]
                   )
        for row in cur.fetchall():
            sense.stagk.append(row[0])

        cur.execute('SELECT gloss FROM glosses WHERE sense_id = ?;', [sense.sense_id])
        for row in cur.fetchall():
            sense.glosses.append(row[0])

        senses.append(sense)

    cur.execute('SELECT frequent FROM entries WHERE entry_id = ?;', [entry_id])
    if cur.fetchone()[0] == 1:
        frequent = True
    else:
        frequent = False

    return Entry(entry_id=entry_id,
                 kanjis=kanjis,
                 readings=readings,
                 senses=senses,
                 frequent=frequent)

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
