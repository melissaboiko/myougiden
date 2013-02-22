import errno
import os

from myougiden import config
from myougiden.color import fmt

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

    cur.execute('''
    SELECT dbversion, jmdict_mtime
    FROM versions;
    ''')
    row = cur.fetchone()
    dbversion = row[0]
    jmdict_mtime = row[1]

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
    fmt(config['core']['version'], 'parameter'),
    fmt(dbversion, 'parameter'),
    fmt(jmdict_mtime, 'parameter'),
    fmt(platform.python_version(), 'parameter'),
    fmt(platform.platform(), 'parameter'),

    fmt(config['paths']['prefix'], 'parameter'),

    fmt(romkan.__version__, 'parameter'),
    # fmt(termcolor.__version__, 'parameter'),
    fmt(argparse.__version__, 'parameter'),
    fmt(psutil_version, 'parameter'),

    scripts['gzip'],
    scripts['rsync'],
    scripts['nice'],
    scripts['ionice'],
    ))
