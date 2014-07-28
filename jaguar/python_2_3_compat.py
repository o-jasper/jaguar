# Here for python version compatibility.

import sys

if sys.version_info.major == 2:
    def to_str(val):  # Python 2
        return unicode(val)
    def is_str(val):
        return type(val) in [str, unicode]
else:
    def to_str(val): # ..3
        return str(val)
    def is_str(val):
        return type(val) is str
