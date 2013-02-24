from myougiden import config
from myougiden import search
from myougiden import color
from myougiden.color import fmt

class Entry():
    '''Equivalent to JMdict entry.'''
    def __init__(self,
                 ent_seq=None, # JMdict ID
                 kanjis=None, # list of Kanjis()
                 readings=None, # list of Readings()
                 senses=None, # list of Senses
                ):
        self.ent_seq = ent_seq
        self.kanjis = kanjis or []
        self.readings = readings or []
        self.senses = senses or []

    def is_frequent(self):
        for kanji in self.kanjis:
            if kanji.frequent:
                return True
        for reading in self.readings:
            if reading.frequent:
                return True

    def remove_orphan_senses(self):
        '''Remove restricted senses that don't match any readings/kanjis.

        Helper function for process_restrictions().
        '''

        # buffer
        ts = None
        for s in self.senses[:]:
            if s.stagr:
                if not ts: ts = [r.text for r in self.readings]
                for stagr in s.stagr:
                    if stagr not in ts:
                        self.senses.remove(s)

        ts = None
        for s in self.senses[:]:
            if s.stagk:
                if not ts: ts = [k.text for k in self.kanjis]
                for stagk in s.stagk:
                    if stagk not in ts:
                        self.senses.remove(s)

    def remove_orphan_readings(self):
        '''Remove restricted senses that don't match any readings/kanjis.

        Helper function for process_restrictions().
        '''
        # buffer
        ts = None

        for r in self.readings[:]:
            if r.re_restr:
                if not ts: ts = [k.text for k in self.kanjis]
                for restr in r.re_restr:
                    if restr not in ts:
                        self.readings.remove(r)

    def process_restrictions(self, search_params):
        '''Remove parts of entry not matching search_params.'''

        matchreg = search.matched_regexp(search_params)

        if search_params['field'] == 'kanji':
            # show only matched kanjis.
            self.kanjis = [k for k in self.kanjis
                           if matchreg.search(k.text)]

            # show only readings & senses that apply to matching kanji.
            self.remove_orphan_readings()
            self.remove_orphan_senses()


        if search_params['field'] == 'reading':
            # we show all readings, even unmatched ones (matched ones will be
            # highlighted).

            # however, if all matched readings are restricted, we remove kanjis
            # not applying to the restriction (it would be silly to show the
            # user 黄葉 when they asked for もみじ).
            matched = [r for r in self.readings
                       if matchreg.search(r.text)]

            restricted = [r for r in matched
                          if r.re_restr]

            if matched == restricted:
                restrictions = []
                for r in restricted:
                    for restr in r.re_restr:
                        restrictions.append(restr)

                self.kanjis = [k for k in self.kanjis
                               if k.text in restrictions]

                self.remove_orphan_readings()
                self.remove_orphan_senses()

            # we DO show senses where stagr doesn't match the queried reading.
            # the rationale is that, since we're showing all readings, it would
            # be confusing to omit other reading's senses.  the display will
            # show the restriction between brackets.

        elif search_params['field'] == 'gloss':
            # consider all *matching* senses.
            # - if at least one of them has no stagk, all kanji apply to it.
            #   so we show all kanji.
            # - but if all of them are restricted, we filter out all kanjis
            #   that don't apply to any senses.
            #
            # likewise for readings and stagr.
            #
            # finally, we remove orphan senses that only applied to
            # kanji/reading removed above.

            changed=False
            matched = []
            for s in self.senses:
                for g in s.glosses:
                    if matchreg.search(g):
                        matched.append(s)
                        break

            restricted = [s for s in matched if s.stagk]
            if matched == restricted:
                # then some kanji may be spurious

                restrictions = []
                for s in matched:
                    for stagk in s.stagk:
                        restrictions.append(stagk)

                for kanji in self.kanjis[:]:
                    if kanji.text not in restrictions:
                        self.kanjis.remove(kanji)
                        changed=True

            restricted = [s for s in matched if s.stagr]
            if matched == restricted:
                # then some readings may be spurious

                restrictions = []
                for s in matched:
                    for stagr in s.stagr:
                        restrictions.append(stagr)

                for reading in self.readings[:]:
                    if reading.text not in restrictions:
                        self.readings.remove(reading)
                        changed=True

            if changed:
                 self.remove_orphan_readings()
                 self.remove_orphan_senses()


    # this thing really needs to be better thought of
    def format_tsv(self, search_params, romajifn=None):
        self.process_restrictions(search_params)
        matchreg = search.matched_regexp(search_params)

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

        s += rsep.join([r.fmt(search_params)
                        for r in self.readings])
        s += "\t" + ksep.join([k.fmt(search_params)
                               for k in self.kanjis])

        for sense in self.senses:
            tagstr = sense.tagstr(search_params)
            if tagstr: tagstr += ' '

            s += "\t%s%s" % (tagstr, gsep.join(sense.glosses))

        if self.is_frequent():
            s += ' ' + fmt('(P)', 'highlight')

        return s

    def format_human(self, search_params, romajifn=None):
        self.process_restrictions(search_params)
        matchreg = search.matched_regexp(search_params)

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
                s += ksep.join([k.fmt(search_params) for k in self.kanjis])
                s += rpar % (rsep.join([r.fmt(search_params) for r in self.readings]))
            else:
                ks = []
                for k in self.kanjis:
                    my_r = [r.fmt(search_params) for r in self.readings
                            if not r.re_restr or k.text in r.re_restr]
                    ks.append(k.fmt(search_params)
                              + rpar % (rsep.join(my_r)))
                s += ksep.join(ks)
        else:
            s += rsep.join([r.fmt(search_params) for r in self.readings])


        for sensenum, sense in enumerate(self.senses, start=1):
            sn = fmt('%d.' % sensenum, 'misc')

            tagstr = sense.tagstr(search_params)
            if tagstr: tagstr += ' '

            s += "\n%s %s%s" % (sn,
                                tagstr,
                                gsep.join(sense.fmt_glosses(search_params)))
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

    def fmt(self, search_params=None):
        if search_params and search_params['field'] == 'kanji':
            matchreg = search.matched_regexp(search_params)
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

    def fmt(self, search_params=None):
        if self.romaji:
            t = self.romaji(self.text)
        else:
            t = self.text

        if search_params and search_params['field'] == 'reading':
            matchreg = search.matched_regexp(search_params)
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

    def fmt_glosses(self, search_params=None):
        '''Return list of formatted strings, one per gloss.'''

        if search_params and search_params['field'] == 'gloss':
            matchreg = search.matched_regexp(search_params)
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

    cur.execute('''SELECT
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

    cur.execute('''SELECT
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

        cur.execute('''SELECT re_restr
                    FROM reading_restrictions
                    WHERE reading_id = ?;''',
                    [reading.reading_id])
        for row in cur.fetchall():
            reading.re_restr.append(row[0])

        readings.append(reading)


    senses = []
    cur.execute(
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

        cur.execute('''
                    SELECT stagk
                    FROM sense_kanji_restrictions
                    WHERE sense_id = ?;
                    ''', [sense.sense_id]
                   )
        for row in cur.fetchall():
            sense.stagk.append(row[0])

        cur.execute('''
                    SELECT stagr
                    FROM sense_reading_restrictions
                    WHERE sense_id = ?;
                    ''', [sense.sense_id]
                   )
        for row in cur.fetchall():
            sense.stagr.append(row[0])

        cur.execute('SELECT gloss FROM glosses WHERE sense_id = ?;', [sense.sense_id])
        for row in cur.fetchall():
            sense.glosses.append(row[0])

        senses.append(sense)

    return Entry(ent_seq=ent_seq,
                 kanjis=kanjis,
                 readings=readings,
                 senses=senses)

def short_expansion(cur, abbrev):
    cur.execute(''' SELECT short_expansion FROM abbreviations WHERE abbrev = ? ;''', [abbrev])
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
    cur.execute('''
    SELECT abbrev
    FROM abbreviations
    ORDER BY abbrev
    ;''')

    abbrevs=[]
    for row in cur.fetchall():
        abbrevs.append(row[0])
    return "\n".join([abbrev_line(cur, abbrev) for abbrev in abbrevs])
