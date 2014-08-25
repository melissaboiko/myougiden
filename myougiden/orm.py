from myougiden import config
from myougiden import search
from myougiden import color
from myougiden import database
from myougiden.color import fmt

class Entry():
    '''Equivalent to JMdict entry.'''
    def __init__(self,
                 ent_seq=None, # JMdict ID
                 frequent=False, # similar to EDICT (P)
                 kanjis=None, # list of Kanjis()
                 readings=None, # list of Readings()
                 senses=None, # list of Senses
                ):
        self.ent_seq = ent_seq
        self.kanjis = kanjis or []
        self.readings = readings or []
        self.senses = senses or []
        self.frequent = frequent

    def is_frequent(self):
        # TODO: more fine-grained
        return self.frequent


    # this thing really needs to be better thought of
    def format_tsv(self, search_conds, romajifn=None):
        matchreg = search.matched_regexp(search_conds)

        # as of 2012-02-22, no kanji or reading field uses full-width
        # semicolon.
        ksep = fmt('；', 'subdue')

        if romajifn:
            # ascii comma is free, too
            rsep = fmt(',', 'subdue')
            for r in self.readings:
                r.romaji = romajifn
        else:
            rsep = fmt('；', 'subdue')

        # as of 2012-02-22, only one entry uses '|' .
        # and it's "c|net", which should be "CNET" anyway.
        gsep = fmt('|', 'subdue')

        # escape separator
        for sense in self.senses:
            for idx, gloss in enumerate(sense.glosses):
                # I am unreasonably proud of this solution.
                sense.glosses[idx] = sense.glosses[idx].replace(gsep, '¦')


        s = ''

        s += rsep.join([r.fmt(search_conds)
                        for r in self.readings])
        s += "\t" + ksep.join([k.fmt(search_conds)
                               for k in self.kanjis])

        for sense in self.senses:
            tagstr = sense.tagstr(search_conds)
            if tagstr: tagstr += ' '

            s += "\t%s%s" % (tagstr, gsep.join(sense.glosses))

        if self.is_frequent():
            s += ' ' + fmt('(P)', 'highlight')

        return s

    def format_human(self, search_conds, romajifn=None):
        matchreg = search.matched_regexp(search_conds)

        ksep = fmt('；', 'subdue')

        if romajifn:
            rsep = fmt(', ', 'subdue')
            for r in self.readings:
                r.romaji = romajifn
        else:
            rsep = fmt('、', 'subdue')

        gsep = fmt('; ', 'subdue')
        rpar = (fmt('（', 'subdue')
                + '%s'
                + fmt('）', 'subdue'))

        s = ''

        if self.is_frequent():
            s += fmt('※', 'highlight') + ' '


        has_re_restr = False
        for r in self.readings:
            if r.re_restr:
                has_re_restr = True
                break

        if self.kanjis:
            if not has_re_restr:
                s += ksep.join([k.fmt(search_conds) for k in self.kanjis])
                s += rpar % (rsep.join([r.fmt(search_conds) for r in self.readings]))
            else:
                ks = []
                for k in self.kanjis:
                    my_r = [r.fmt(search_conds) for r in self.readings
                            if not r.re_restr or k.text in r.re_restr]
                    ks.append(k.fmt(search_conds)
                              + rpar % (rsep.join(my_r)))
                s += ksep.join(ks)
        else:
            s += rsep.join([r.fmt(search_conds) for r in self.readings])


        for sensenum, sense in enumerate(self.senses, start=1):
            sn = fmt('%d.' % sensenum, 'misc')

            tagstr = sense.tagstr(search_conds)
            if tagstr: tagstr += ' '

            s += "\n%s %s%s" % (sn,
                                tagstr,
                                gsep.join(sense.fmt_glosses(search_conds)))
        return s

class Kanji():
    '''Equivalent to JMdict <k_ele>.'''
    def __init__(self,
                 kanji_id=None,
                 text=None, # = keb
                 frequent=False,
                 ke_inf=None):
        self.kanji_id = kanji_id
        self.text = text
        self.frequent = frequent
        self.ke_inf = ke_inf

    def fmt(self, search_conds=None):
        if search_conds and search_conds.field == 'kanji':
            matchreg = search.matched_regexp(search_conds)
            t = color.color_regexp(matchreg,
                                      self.text,
                                      'kanji',
                                      'matchjp')
        else:
            t = fmt(self.text, 'kanji')

        if self.ke_inf:
            t = t + fmt('[' + self.ke_inf + ']', 'subdue')
        return t


class Reading():
    '''Equivalent to JMdict <r_ele>.'''
    def __init__(self,
                 reading_id=None,
                 text=None, # = reb
                 re_nokanji=False,
                 re_restr=None,
                 re_inf=None,
                 frequent=False,

                 # None or a function
                 romaji=None,
                ):
        self.reading_id = reading_id
        self.text = text
        self.re_nokanji = re_nokanji
        self.re_restr = re_restr or []
        self.re_inf = re_inf
        self.frequent = frequent
        self.romaji = romaji

    def fmt(self, search_conds=None):
        if self.romaji:
            t = self.romaji(self.text)
        else:
            t = self.text

        if search_conds and search_conds.field == 'reading':
            matchreg = search.matched_regexp(search_conds)
            t = color.color_regexp(matchreg,
                                      t,
                                      'reading',
                                      'matchjp')
        else:
            t = fmt(t, 'reading')

        if self.re_nokanji:
            t = fmt('＊', 'subdue') + t
        if self.re_inf:
            t = t + fmt('[' + self.re_inf + ']', 'subdue')
        return t


class Sense():
    '''Equivalent to JMdict <sense>.

    Attributes:
    - sense_id: database ID.
    - glosses: a list of glosses (as strings).
    '''

    def __init__(self,
                 sense_id=None,

                 # glosses, a list of strings
                 glosses=None,

                 # restrictions, as lists of strings
                 stagk=None,
                 stagr=None,

                 # each is a string of abbreviations separated by ';'
                 pos=None,
                 field=None,
                 misc=None,
                 s_inf=None,

                 # arbitrary string
                 dial=None,

                 # TODO
                 # lsource=None,
                ):
        self.sense_id = sense_id

        self.glosses = glosses or list()

        self.stagk = stagk or list()
        self.stagr = stagr or list()

        self.pos = pos
        self.field = field
        self.misc = misc
        self.dial = dial

        self.s_inf = s_inf


    def tagstr(self, search_conditions):
        '''Return a string with all information tags.

        Automatic colors depending on myougiden.color.use_color .'''

        tagstr = ''
        tags = []
        for attr in ('pos', 'field', 'misc', 'dial'):
            tag = getattr(self, attr)
            if tag:
                tags.append(tag)
        if len(tags) > 0:
            tagstr += '[%s]' % (';'.join(tags))

        if self.s_inf:
            if len(tagstr) > 0:
                tagstr += ' '
            tagstr += '[%s]' % self.s_inf

        if self.stagk or self.stagr:
            if len(tagstr) > 0:
                tagstr += ' '
            tagstr += '〔%s〕' % '、'.join(self.stagk + self.stagr)

        if len(tagstr) > 0:
            return fmt(tagstr, 'subdue')
        else:
            return ''

    def fmt_glosses(self, search_conds=None):
        '''Return list of formatted strings, one per gloss.'''

        if search_conds and search_conds.field == 'gloss':
            matchreg = search.matched_regexp(search_conds)
            return [color.color_regexp(matchreg,
                                       gloss)
                   for gloss in self.glosses]
        else:
            return [gloss for gloss in self.glosses]


def fetch_entry(cur, ent_seq):
    '''Return Entry object..'''

    kanjis = []
    readings = []
    senses = []

    database.execute(cur, '''SELECT
                kanji_id,
                kanji,
                ke_inf,
                frequent
                FROM kanjis
                WHERE ent_seq = ?;''', [ent_seq])
    for row in cur.fetchall():
        kanjis.append(Kanji(
            kanji_id=row[0],
            text=row[1],
            ke_inf=row[2],
            frequent=row[3],
        ))

    database.execute(cur, '''SELECT
                reading_id,
                reading,
                re_nokanji,
                frequent,
                re_inf
                FROM readings
                WHERE ent_seq = ?;''', [ent_seq])

    for row in cur.fetchall():
        reading = Reading(
            reading_id=row[0],
            text=row[1],
            re_nokanji=row[2],
            frequent=row[3],
            re_inf=row[4],
        )

        database.execute(cur, '''SELECT re_restr
                    FROM reading_restrictions
                    WHERE reading_id = ?;''',
                    [reading.reading_id])
        for row in cur.fetchall():
            reading.re_restr.append(row[0])

        readings.append(reading)


    senses = []
    database.execute(cur, 
        '''SELECT
        sense_id,
        pos,
        field,
        misc,
        dial,
        s_inf
        FROM senses
        WHERE ent_seq = ?;''',
        [ent_seq]
    )

    for row in cur.fetchall():
        sense = Sense(sense_id=row[0],
                      pos=row[1],
                      field=row[2],
                      misc=row[3],
                      dial=row[4],
                      s_inf=row[5])

        database.execute(cur, '''
                    SELECT stagk
                    FROM sense_kanji_restrictions
                    WHERE sense_id = ?;
                    ''', [sense.sense_id]
                   )
        for row in cur.fetchall():
            sense.stagk.append(row[0])

        database.execute(cur, '''
                    SELECT stagr
                    FROM sense_reading_restrictions
                    WHERE sense_id = ?;
                    ''', [sense.sense_id]
                   )
        for row in cur.fetchall():
            sense.stagr.append(row[0])

        database.execute(cur, 'SELECT gloss FROM glosses WHERE sense_id = ?;', [sense.sense_id])
        for row in cur.fetchall():
            sense.glosses.append(row[0])

        senses.append(sense)

    database.execute(cur, 'SELECT frequent FROM entries WHERE ent_seq = ?;', [ent_seq])
    frequent=cur.fetchone()[0]

    return Entry(ent_seq=ent_seq,
                 frequent=frequent,
                 kanjis=kanjis,
                 readings=readings,
                 senses=senses,
                )

def short_expansion(cur, abbrev):
    database.execute(cur, ''' SELECT short_expansion FROM abbreviations WHERE abbrev = ? ;''', [abbrev])
    row = cur.fetchone()
    if row:
        return row[0]
    else:
        return None

def abbrev_line(cur, abbrev):
    exp = short_expansion(cur, abbrev)
    if exp:
        abbrev = fmt(abbrev, 'subdue')
        return "%s\t%s" % (abbrev, exp)
    else:
        return None

def abbrevs_table(cur):
    database.execute(cur, '''
    SELECT abbrev
    FROM abbreviations
    ORDER BY abbrev
    ;''')

    abbrevs=[]
    for row in cur.fetchall():
        abbrevs.append(row[0])
    return "\n".join([abbrev_line(cur, abbrev) for abbrev in abbrevs])
