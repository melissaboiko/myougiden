import errno
import os
import re

from myougiden import config
from myougiden.color import fmt

debug = False

# from http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
# convenience function because python < 3.2 has no exist_ok
def mkdir_p(path):
    # safely allows mkdir_p(os.path.dirname('nodirs'))
    if path == '':
        return

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            return
        else:
            raise e


# credits: http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def version(cur):
    import argparse
    import romkan
    # import termcolor # no version
    import platform

    try:
        import psutil
        psutil_version = psutil.__version__
    except ImportError:
        psutil_version = None

    if cur:
        from myougiden import database
        database.execute(cur, '''
                    SELECT dbversion, jmdict_mtime
                    FROM versions;
                    ''')
        row = cur.fetchone()
        dbversion = fmt(row[0], 'parameter')
        jmdict_mtime = fmt(row[1], 'parameter')
    else:
        dbversion = fmt('Database not found!', 'error')
        jmdict_mtime = fmt('Database not found!', 'error')

    if config:
        version = fmt(config.get('core','version'), 'parameter')
        prefix = fmt(config.get('paths','prefix'), 'parameter')
    else:
        version = fmt('Config not found!', 'error')
        prefix = fmt('Config not found!', 'error')

    scripts = {}
    for s in ('gzip', 'rsync', 'nice', 'ionice'):
        path = which(s)
        if path:
            scripts[s] = fmt(path, 'parameter')
        else:
            scripts[s] = fmt(path, 'warning')

    return ('''
myougiden version %s , database v. %s
JMdict last modified %s
Python version %s (%s)
Prefix: %s

Libraries:
  romkan: %s
  argparse: %s
  psutil: %s

External programs:
  gzip: %s
  rsync: %s
  nice: %s
  ionice: %s
'''.strip() % (
    version,
    dbversion,
    jmdict_mtime,
    fmt(platform.python_version(), 'parameter'),
    fmt(platform.platform(), 'parameter'),

    prefix,

    fmt(romkan.__version__, 'parameter'),
    # fmt(termcolor.__version__, 'parameter'),
    fmt(argparse.__version__, 'parameter'),
    fmt(psutil_version, 'parameter'),

    scripts['gzip'],
    scripts['rsync'],
    scripts['nice'],
    scripts['ionice'],
    ))

def color_pager():
    '''Return None, or a color-enabled pager to use.'''
    pager = os.getenv('MYOUGIDENPAGER')

    # trust user to set his color-enabled pager
    if pager: return pager

    # guess
    pager = os.getenv('PAGER')

    if not pager:
        if which('less'):
            pager='less'
            os.environ['LESS'] = 'FRX'
            return pager
        else:
            return None
    elif re.match('less', pager):
        opts = os.getenv('LESS')
        if not opts:
            os.environ['LESS'] = 'FRX'
        elif (re.search('[rR]', os.environ['LESS'])
              or re.search('-[rR]', pager)):
            return pager
        else:
            # damn
            return None
    elif re.match('most|w3m', pager):
        return pager
    else:
        # more(1) works in my machine, but they say some don't?
        # 'vim -' doesn't work
        return None

# credits:
# http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
def get_terminal_size():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

    return int(cr[1]), int(cr[0])

# ISO 632-1 to ISO 632-2
# the first is used by JMdict, the second by system locale.
#
# from http://www.loc.gov/standards/iso639-2/php/code_list.php .
# we use the (B) code, as they appear to be the ones that JMdict prefers.
# thanks to http://www.convertcsv.com/html-table-to-csv.htm .
ISO639_1TO2 = {
'aa': 'aar',
'ab': 'abk',
'af': 'afr',
'ak': 'aka',
'sq': 'alb',
'am': 'amh',
'ar': 'ara',
'an': 'arg',
'hy': 'arm',
'as': 'asm',
'av': 'ava',
'ae': 'ave',
'ay': 'aym',
'az': 'aze',
'ba': 'bak',
'bm': 'bam',
'eu': 'baq',
'be': 'bel',
'bn': 'ben',
'bh': 'bih',
'bi': 'bis',
'bo': 'tib',
'bs': 'bos',
'br': 'bre',
'bg': 'bul',
'my': 'bur',
'ca': 'cat',
'cs': 'cze',
'ch': 'cha',
'ce': 'che',
'zh': 'chi',
'cu': 'chu',
'cv': 'chv',
'kw': 'cor',
'co': 'cos',
'cr': 'cre',
'cy': 'wel',
'cs': 'cze',
'da': 'dan',
'de': 'ger',
'dv': 'div',
'nl': 'dut',
'dz': 'dzo',
'el': 'gre',
'en': 'eng',
'eo': 'epo',
'et': 'est',
'eu': 'baq',
'ee': 'ewe',
'fo': 'fao',
'fa': 'per',
'fj': 'fij',
'fi': 'fin',
'fr': 'fre',
'fr': 'fre',
'fy': 'fry',
'ff': 'ful',
'ka': 'geo',
'de': 'ger',
'gd': 'gla',
'ga': 'gle',
'gl': 'glg',
'gv': 'glv',
'el': 'gre',
'gn': 'grn',
'gu': 'guj',
'ht': 'hat',
'ha': 'hau',
'he': 'heb',
'hz': 'her',
'hi': 'hin',
'ho': 'hmo',
'hr': 'hrv',
'hu': 'hun',
'hy': 'arm',
'ig': 'ibo',
'is': 'ice',
'io': 'ido',
'ii': 'iii',
'iu': 'iku',
'ie': 'ile',
'ia': 'ina',
'id': 'ind',
'ik': 'ipk',
'is': 'ice',
'it': 'ita',
'jv': 'jav',
'ja': 'jpn',
'kl': 'kal',
'kn': 'kan',
'ks': 'kas',
'ka': 'geo',
'kr': 'kau',
'kk': 'kaz',
'km': 'khm',
'ki': 'kik',
'rw': 'kin',
'ky': 'kir',
'kv': 'kom',
'kg': 'kon',
'ko': 'kor',
'kj': 'kua',
'ku': 'kur',
'lo': 'lao',
'la': 'lat',
'lv': 'lav',
'li': 'lim',
'ln': 'lin',
'lt': 'lit',
'lb': 'ltz',
'lu': 'lub',
'lg': 'lug',
'mk': 'mac',
'mh': 'mah',
'ml': 'mal',
'mi': 'mao',
'mr': 'mar',
'ms': 'may',
'mk': 'mac',
'mg': 'mlg',
'mt': 'mlt',
'mn': 'mon',
'mi': 'mao',
'ms': 'may',
'my': 'bur',
'na': 'nau',
'nv': 'nav',
'nr': 'nbl',
'nd': 'nde',
'ng': 'ndo',
'ne': 'nep',
'nl': 'dut',
'nn': 'nno',
'nb': 'nob',
'no': 'nor',
'ny': 'nya',
'oc': 'oci',
'oj': 'oji',
'or': 'ori',
'om': 'orm',
'os': 'oss',
'pa': 'pan',
'fa': 'per',
'pi': 'pli',
'pl': 'pol',
'pt': 'por',
'ps': 'pus',
'qu': 'que',
'rm': 'roh',
'ro': 'rum',
'ro': 'rum',
'rn': 'run',
'ru': 'rus',
'sg': 'sag',
'sa': 'san',
'si': 'sin',
'sk': 'slo',
'sk': 'slo',
'sl': 'slv',
'se': 'sme',
'sm': 'smo',
'sn': 'sna',
'sd': 'snd',
'so': 'som',
'st': 'sot',
'es': 'spa',
'sq': 'alb',
'sc': 'srd',
'sr': 'srp',
'ss': 'ssw',
'su': 'sun',
'sw': 'swa',
'sv': 'swe',
'ty': 'tah',
'ta': 'tam',
'tt': 'tat',
'te': 'tel',
'tg': 'tgk',
'tl': 'tgl',
'th': 'tha',
'bo': 'tib',
'ti': 'tir',
'to': 'ton',
'tn': 'tsn',
'ts': 'tso',
'tk': 'tuk',
'tr': 'tur',
'tw': 'twi',
'ug': 'uig',
'uk': 'ukr',
'ur': 'urd',
'uz': 'uzb',
've': 'ven',
'vi': 'vie',
'vo': 'vol',
'cy': 'wel',
'wa': 'wln',
'wo': 'wol',
'xh': 'xho',
'yi': 'yid',
'yo': 'yor',
'za': 'zha',
'zh': 'chi',
'zu': 'zul',
}

# TODO: get from the XML at updatedb time
JMDICT_LANGS = [
    'dut',
    'eng',
    'fre',
    'ger',
    'hun',
    'rus',
    'slv',
    'spa',
    'swe',
]
