import configparser
import re
import os
import sys

def read_config(prefix, rel='etc/myougiden/config.ini'):
    path = os.path.join(prefix, rel)
    if os.path.isfile(path):
        cp = configparser.ConfigParser()
        cp.read(path)
        cp.set('paths', 'prefix', prefix)
        return cp
    else:
        return None

def find_config():
    # detect installation prefix. is there a better way of doing this?

    dirname = os.path.dirname(__file__)

    prefixes = []
    prefixes.append(os.path.realpath(os.path.join(dirname, '..')))
    if re.search('/lib/', dirname):
        prefixes.append(re.sub('/lib/.*', '', dirname))
    prefixes.append(sys.prefix)

    for prefix in prefixes:
        cp = read_config(prefix)
        if cp: return cp

    return None

config = find_config()
