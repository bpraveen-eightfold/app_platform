from __future__ import absolute_import

import six

def safe_long(i):
    return long(i) if six.PY2 else int(i) # pylint: disable=undefined-variable
