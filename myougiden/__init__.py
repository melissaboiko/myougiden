import configparser
import re
import os

def read_config():
    cp = configparser.ConfigParser()
    dirname = os.path.dirname(__file__)

    # default for running from source dir
    prefix = os.path.realpath(os.path.join(dirname, '..'))
    config_path = os.path.join(prefix, 'etc/config.ini')

    # detect installation prefix.
    # is there a better way of doing this?
    if re.search('/lib/', dirname):
        prefix = re.sub('/lib/.*', '', dirname)
        config_path = os.path.join(prefix, 'etc/myougiden/config.ini')

    if not os.path.isfile(config_path):
        raise RuntimeError("ERROR: couldn't find config.ini at %s" % config_path)

    cp.read(os.path.join(prefix, config_path))
    cp.set('paths','prefix',prefix)
    return cp

config = read_config()
