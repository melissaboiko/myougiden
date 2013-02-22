import re

# extracted from edict "reading" fields. TODO: cross-check with Unicode
edict_kana='・？ヽヾゝゞー〜ぁあぃいうぇえおかがきぎくぐけげこごさざしじすずせぜそぞただちっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろわゐゑをんァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヶ'
edict_kana_regexp=re.compile("^[%s]+$" % edict_kana)

latin_regexp=re.compile(r'^[\]\-'
                       + r' !"#$%&()*+,./:;<=>?@\\^_`{}|~‘’“”'
                       + "'"
                       + 'a-zA-Z0-9'
                       + ']+$')
def is_latin(string):
    return latin_regexp.match(string) is not None

romaji_regexp=re.compile(r'^[\]\-'
                         + r' !"#$%&()*+,./:;<=>?@\\^_`{}|~‘’“”'
                         + "'"
                         + 'a-zA-Z0-9'
                         + 'āēīōūĀĒĪŌŪâêîôûÂÊÎÔÛ'
                         + ']+$')
def is_romaji(string):
    return romaji_regexp.match(string) is not None
def is_kana(string):
    return edict_kana_regexp.match(string) is not None

class MatchesNothing():
    '''Fake regexp object that matches nothing.

    We use this because, when running database searches, it's faster than
    trying to compile a regexp and failing once per row.  We only need a
    singleton object.'''

    def search(self, string, flags=0):
        return None
    def match(self, string, flags=0):
        return None

matchesnothing = MatchesNothing()


regexp_store = {}
def get_regexp(pattern, flags):
    '''Return a compiled regexp from persistent store; make one if needed.

    We use this helper function so that the SQL hooks don't have to
    compile the same regexp at every query.

    Warning: Flags are not part of the hash. In other words, this function
    doesn't work for the same pattern with different flags.
    '''

    if pattern in regexp_store.keys():
        return regexp_store[pattern]
    else:
        try:
            comp = re.compile(pattern, re.U | flags)
            regexp_store[pattern] = comp
            return comp
        except re.error:
            regexp_store[pattern] = matchesnothing
            return matchesnothing

def has_regexp_special(string):
    '''True if string has special characters of regular expressions.'''
    special = re.compile('[%s]' % re.escape(r'.^$*+?{}()[]\|'))
    return special.search(string)

romaji_expansions = {
    'ā': 'aa',
    'â': 'aa',
    'ī': 'ii',
    'î': 'ii',
    'ū': 'uu',
    'û': 'uu',
}
romaji_expansions_o = [{'ō': 'ou', 'ô': 'ou'},
                       {'ō': 'oo', 'ô': 'oo'}]
romaji_expansions_e = [{'ē': 'ei', 'ê': 'ei'},
                       {'ē': 'ee', 'ê': 'ee'}]

def expand_romaji(string):
    '''kā -> [kaa] ; kāmyō -> [kaamyou, kaamyoo] '''

    for char, rep in romaji_expansions.items():
        string = string.replace(char, rep)

    variations = []
    for o in romaji_expansions_o:
        for e in romaji_expansions_e:
            var = string[:]
            for char, rep in o.items():
                var = var.replace(char, rep)
            for char, rep in e.items():
                var = var.replace(char, rep)
            if var not in variations:
                variations.append(var)
    return variations

