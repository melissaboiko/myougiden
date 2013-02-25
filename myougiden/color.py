import termcolor
import os
import re
import sys

# don't you love globals
use_color = False

# style : args
# *args as for colored()
DARKBG={
    # color problems:
    # - japanese bitmap fonts are kinda crummy in bold
    # - non-bold grey doesn't even show in my dark xterm
    # - green/red is the most common color blindness
    # - it's very hard to impossible to detect if bg is dark or light
    # - cyan is better for dark bg, blue for light. green and yellow are often
    #   bad for light.

    'reading': ('magenta', None, None),
    'kanji': ('cyan', None, None),
    'misc': ('green', None, None),
    'highlight': ('green', None, ['bold']),
    'subdue': ('yellow', None, None),

    'match': ('red', None, ['bold']),
    'matchjp': ('red', None, None),

    'info': ('magenta', None, None),
    'warning': ('yellow', None, ['bold']),
    'error': ('red', None, ['bold']),
    'parameter': ('green', None, None),

    'starting': ('red', None, ['bold']),
    'midway': ('yellow', None, ['bold']),
    'finishing': ('blue', None, ['bold']),
    'done': ('cyan', None, ['bold']),
}

LIGHTBG={
    'reading': ('magenta', None, None),
    'kanji': ('blue', None, None),
    'misc': ('grey', None, None),
    'highlight': (None, None, ['bold']),
    'subdue': ('grey', None, None),
    'match': ('red', None, ['bold']),
    'matchjp': ('red', None, None),
    'info': ('blue', None, None),
    'warning': ('magenta', None, ['bold']),
    'error': ('red', None, ['bold']),
    'parameter': ('green', None, None),
    'starting': ('red', None, ['bold']),
    'midway': ('grey', None, ['bold']),
    'finishing': ('magenta', None, ['bold']),
    'done': ('blue', None, ['bold']),
}

style=DARKBG

def coloredp(string, color=None, on_color=None, attrs=None):
    if use_color:
        return termcolor.colored(string,
                                 color=color, on_color=on_color, attrs=attrs)
    else:
        return string

# convenience function to turn on bold
def coloredpb(string, color):
    return coloredp(string, color=color, attrs=['bold'])

def fmt(string, sty):
    return coloredp(string, *(style[sty]))

def percent(string, percent):
    if not use_color:
        return string
    if percent < 0.33:
        return fmt(string, 'starting')
    elif percent < 0.66:
        return fmt(string, 'midway')
    elif percent < 1:
        return fmt(string, 'finishing')
    else:
        return fmt(string, 'done')

def color_regexp(reg_obj, longstring, base_style=None, match_style='match'):
    '''Search regexp in longstring; return longstring with match colored.'''

    if not use_color:
        return longstring

    m = reg_obj.search(longstring)
    if not m:
        if base_style:
            return fmt(longstring, base_style)
        else:
            return longstring
    else:
        head = longstring[:m.start()]
        tail = longstring[m.end():]
        if base_style:
            head = fmt(head, base_style)
            tail = fmt(tail, base_style)
        return head + fmt(m.group(), match_style) + tail

# credit: http://stackoverflow.com/questions/596216/formula-to-determine-brightness-of-rgb-color
def luma(rgbhex):
    '''Retuns between 0 and 255.'''
    rgb = rgbhex.lstrip('#')
    return ((0.299 * int(rgb[0:2], 16))
            + (0.587 * int(rgb[2:4], 16))
            + (0.114 * int(rgb[4:6], 16)))

def guess_background():
    # our own variable; not in any standard
    v = os.getenv('BACKGROUND')
    if v == 'dark':
        return 'dark'
    elif v == 'light':
        return 'light'

    # this basically works only for rxvt. vim uses it.
    v = os.getenv('COLORFGBG')
    if v:
        bg = int(v.split(';')[-1])
        if (0 <= bg <= 6) or (bg == 8):
            return 'dark'
        else:
            return 'light'

    # speaking of vim...
    vimrc = os.path.expanduser('~/.vimrc')
    if os.path.isfile(vimrc):
        with open(vimrc, 'r') as f:
            for line in f:
                m = re.match('[^"]*set.*background.*=([a-z]*)', line)
                if m:
                    if m.group(1) == 'dark':
                        return 'dark'
                    elif mgroup(1) == 'light':
                        return 'light'
                    break

    if os.getenv('DISPLAY') and sys.platform not in ('darwin', 'mac'):
        # on X there'x xrdb, but it seems little reliable here. last guess.

        # we also don't run this test on OS X (darwin), since it triggers the X
        # server and slow down a lot.
        from myougiden import common
        xrdb = common.which('xrdb')
        if xrdb:
            import subprocess
            p = subprocess.Popen(['xrdb', '-query'], stdout=subprocess.PIPE)
            p.wait()
            for line in p.stdout:
                if re.search(b'background:', line):
                    rgb = line.strip().split()[-1].decode()
                    if luma(rgb) > 128:
                        return 'light'
                    else:
                        return 'dark'


    # TODO: there's a very complex method to query xterm.
    # but it's complex, and screen breaks it anyway.

    return None

