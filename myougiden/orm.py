import myougiden.color
from myougiden.color import fmt, color_regexp
from myougiden.common import matched_regexp

class Entry():
    '''Equivalent to JMdict entry.'''
    def __init__(self,
                 ent_seq=None,
                 kanjis=None, # list of Kanjis()
                 readings=None, # list of Readings()
                 senses=None, # list of Senses
                 frequent=False
                ):
        self.ent_seq = ent_seq
        self.kanjis = kanjis or []
        self.readings = readings or []
        self.senses = senses or []
        self.frequent = frequent

    # TODO: more detailed
    def is_frequent(self):
        return self.frequent

    def colorize(self, search_params):
        '''Alter child elements to add color, including the matched search.'''

        if not myougiden.color.use_color:
            return

        matchreg = matched_regexp(search_params)
        if search_params['field'] == 'reading':
            for reading in self.readings:
                reading.colorize(matchreg=matchreg)
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

    # this thing really needs to be better thought of
    def format_tsv(self, search_params, romajifn=None):
        self.colorize(search_params)

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
            s += fmt('(P)', 'highlight')

        return s


    def format_human(self, search_params, romajifn=None):
        self.colorize(search_params)

        sep_full = fmt('；', 'subdue')
        sep_half = fmt(';', 'subdue')


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
                 id=None,
                 text=None, # = keb
                 frequent=False,
                 inf=None):
        self.id = id
        self.text = text
        self.frequent = frequent
        self.inf = inf

    def colorize(self, matchreg=None):
        if matchreg:
            self.text = color_regexp(matchreg, self.text, 'kanji')
        else:
            self.text = fmt(self.text, 'kanji')


class Reading():
    '''Equivalent to JMdict <r_ele>.'''
    def __init__(self,
                 id=None,
                 text=None, # = reb
                 frequent=False,
                 inf=None,
                ):
        self.id = id
        self.text = text
        self.frequent = frequent
        self.inf = inf

    def colorize(self, matchreg=None):
        if matchreg:
            self.text = color_regexp(matchreg, self.text, 'reading')
        else:
            self.text = fmt(self.text, 'reading')

class Sense():
    '''Equivalent to JMdict <sense>.

    Attributes:
    - glosses: a list of glosses (as strings).
    - pos: part-of-speech.
    - misc: other info, abbreviated.
    - dial: dialect.
    - s_inf: long case-by-case remarks.
    - id: database ID.
    '''

    def __init__(self,
                 id=None,
                 pos=None,
                 misc=None,
                 dial=None,
                 s_inf=None,
                 glosses=None,
                ):
        self.id = id
        self.pos = pos
        self.misc = misc
        self.dial = dial
        self.s_inf = s_inf
        self.glosses = glosses or list()

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

        return fmt(tagstr, 'subdue')

    def colorize(self, matchreg=None):
        '''Colorizes glosses if matchreg is not None.'''

        if matchreg:
            for idx, gloss in enumerate(self.glosses):
                self.glosses[idx] = color_regexp(matchreg, gloss)

def fetch_entry(cur, ent_seq):
    '''Return Entry object..'''

    kanjis = []
    readings = []
    senses = []

    cur.execute('SELECT id, kanji FROM kanjis WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        # TODO: k_inf, kpri
        kanjis.append(Kanji(
            id=row[0],
            text=row[1],
        ))

    cur.execute('SELECT id, reading FROM readings WHERE ent_seq = ?;', [ent_seq])
    for row in cur.fetchall():
        # TODO: r_inf, rpri
        readings.append(Reading(
            id=row[0],
            text=row[1]
        ))

    senses = []
    cur.execute(
        'SELECT id, pos, misc, dial, s_inf FROM senses WHERE ent_seq = ?;',
        [ent_seq]
    )
    for row in cur.fetchall():
        sense = Sense(id=row[0],
                      pos=row[1],
                      misc=row[2],
                      dial=row[3],
                      s_inf=row[4])

        cur.execute('SELECT gloss FROM glosses WHERE sense_id = ?;', [sense.id])
        for row in cur.fetchall():
            sense.glosses.append(row[0])

        senses.append(sense)

    cur.execute('SELECT frequent FROM entries WHERE ent_seq = ?;', [ent_seq])
    if cur.fetchone()[0] == 1:
        frequent = True
    else:
        frequent = False


    return Entry(ent_seq=ent_seq,
                 kanjis=kanjis,
                 readings=readings,
                 senses=senses,
                 frequent=frequent)
