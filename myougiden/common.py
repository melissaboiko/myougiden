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
