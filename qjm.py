# convenience script for interactive use:
# myougiden $ python3.2
# >>> from qjm import *

from myougiden import config
from xml.etree.cElementTree import ElementTree as ET
import gzip

et = ET()
jm = et.parse(gzip.open(config['paths']['jmdictgz'], 'r'))

from xml.etree.cElementTree import tostring
def tos(element):
    return tostring(element).decode()
