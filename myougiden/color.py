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

