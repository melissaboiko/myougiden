import configparser
import re
import os

def read_config():
    cp = configparser.ConfigParser()
    dirname = os.path.dirname(__file__)

    # default for running from source dir
    prefix = os.path.realpath(os.path.join(dirname, '..'))
    config_path = 'etc/config.ini'

    # detect installation prefix.
    # is there a better way of doing this?
    if re.search('/lib/', dirname):
        prefix = re.sub('/lib/.*', '', dirname)
        config_path = 'etc/myougiden/config.ini'

    cp.read(os.path.join(prefix, config_path))
    cp.set('paths','prefix',prefix)
    return cp

config = read_config()
