from __future__ import absolute_import

import re
import six
import str_utils

class RegexMatch(object):
    
    def __init__(self, match_obj):
        self.match_obj = match_obj

    @staticmethod
    def _convert_to_str(val):
        if not val:
            return val
        if isinstance(val, tuple):
            out = (str_utils.maybe_convert_bytes_to_str(a) for a in val)
            return tuple(out)
        if isinstance(val, six.binary_type):
            return str_utils.maybe_convert_bytes_to_str(val)
        return val

    def groupdict(self):
        group_dict = self.match_obj.groupdict()
        if not group_dict:
            return group_dict
        for k, v in group_dict.items():
            group_dict[k] = RegexMatch._convert_to_str(v)
        return group_dict

    def groups(self):
        return RegexMatch._convert_to_str(self.match_obj.groups())

    def group(self, *args):
        return RegexMatch._convert_to_str(self.match_obj.group(*args))

    def __bool__(self):
        return bool(self.match_obj)

def search(regex, val, flags=0):
    mat = re.search(regex, val, flags=flags)
    return RegexMatch(mat) if mat else None
