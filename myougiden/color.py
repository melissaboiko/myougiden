import termcolor
import re
from myougiden.texttools import get_regexp

# don't you love globals
use_color = False

# style : args
# *args as for colored()
STYLES={
    # color problems:
    # - japanese bitmap fonts are kinda crummy in bold
    # - non-bold gray doesn't even show in my dark xterm
    # - green/red is the most common color blindness
    # - it's very hard to impossible to detect if bg is dark or light
    # - cyan is better for dark bg, blue for light

    'reading': ('magenta', None, None),

    'kanji': ('cyan', None, None),

    # default
    # 'gloss':

    'misc': ('green', None, None),
    'highlight': ('green', None, ['bold']),

    'subdue': ('yellow', None, None),

    'match': ('red', None, None),

    'info': ('magenta', None, None),
    'warning': ('yellow', None, None),
    'error': ('red', None, ['bold']),

    'parameter': ('green', None, None),

}

def coloredp(string, color=None, on_color=None, attrs=None):
    if use_color:
        return termcolor.colored(string,
                                 color=color, on_color=on_color, attrs=attrs)
    else:
        return string

# convenience function to turn on bold
def coloredpb(string, color):
    return coloredp(string, color=color, attrs=['bold'])

def fmt(string, style):
    return coloredp(string, *(STYLES[style]))

def color_percent(string, percent):
    if not use_color:
        return string
    if percent < 0.33:
        return coloredpb(string, 'red')
    elif percent < 0.66:
        return coloredpb(string, 'yellow')
    elif percent < 1:
        return coloredpb(string, 'blue')
    else:
        return coloredpb(string, 'cyan')

def color_regexp(reg_obj, longstring, base_style=None):
    '''Search regexp in longstring; return longstring with match colored.'''

    if not use_color:
        return longstring

    m = reg_obj.search(longstring)
    if not m:
        return longstring
    else:
        head = longstring[:m.start()]
        tail = longstring[m.end():]
        if base_style:
            head = fmt(head, base_style)
            tail = fmt(tail, base_style)
        return head + fmt(m.group(), 'match') + tail

def colorize_data(kanjis, readings, senses, search_params):
    '''Colorize matched data according to search parameters.

    search_params: A dictionary of arguments like those of search_by().
    '''

    # TODO: there's some duplication between this logic and search_by()

    # regexp to match whatever the query matched
    reg = search_params['query']
    if not search_params['regexp']:
        reg = re.escape(reg)

    if search_params['extent'] == 'whole':
        reg = '^' + reg + '$'
    elif search_params['extent'] == 'word':
        reg = r'\b' + reg + r'\b'

    if search_params['case_sensitive']:
        reg = get_regexp(reg, 0)
    else:
        reg = get_regexp(reg, re.I)

    if search_params['field'] == 'reading':
        readings = [color_regexp(reg, r, 'reading') for r in readings]
        kanjis = [fmt(k, 'kanji') for k in kanjis]
    elif search_params['field'] == 'kanji':
        readings = [fmt(k, 'reading') for k in readings]
        kanjis = [color_regexp(reg, k, 'kanji') for k in kanjis]
    elif search_params['field'] == 'gloss':
        readings = [fmt(k, 'reading') for k in readings]
        kanjis = [fmt(k, 'kanji') for k in kanjis]

        for sense in senses:
            sense.glosses = [color_regexp(reg, g) for g in sense.glosses]

    return (kanjis, readings, senses)
