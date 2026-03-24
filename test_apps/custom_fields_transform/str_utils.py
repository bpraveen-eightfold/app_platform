from __future__ import absolute_import

import six
import int_utils

def maybe_convert_bytes_to_str(inp, ignore=False):
    if isinstance(inp, list) and inp and not six.PY2:
        return [maybe_convert_bytes_to_str(_i, ignore=ignore) for _i in inp]
    if inp is not None and not six.PY2 and isinstance(inp, bytes):
        return inp.decode('utf-8') if not ignore else inp.decode('utf-8', 'ignore')
    return inp

def maybe_str_to_bytes(input_str):
    if not six.PY2 and not isinstance(input_str, bytes):
        return bytes(input_str, 'utf-8')
    return input_str

FALSY_VALUES = set(['0', 'false', 'none', 'null', 'undefined', 'unknown'])
def is_truthy(str_val):
    if not str_val or (isinstance(str_val, six.string_types) and str_val.lower().strip() in FALSY_VALUES):
        return False
    return bool(str_val)

def convert_to_data_type(data_type, value, raise_exception=False):
    import time_utils
    try:
        if data_type == 'bool':
            return int(is_truthy(value))
        elif data_type in ('date', 'datetime'):
            return int(time_utils.to_timestamp(value))
        elif data_type == 'int':
            return int_utils.safe_long(value)
        elif data_type == 'float':
            return float(value)
        return value
    except:
        if not raise_exception:
            return value
        raise

def safe_get_float(s, default=0.0):
    try:
        return float(s) if s not in ['nan', 'NaN'] else default
    except:
        return default

def rchop(input_str, ending, ci=True):
    if input_str.endswith(ending) or (ci and input_str.lower().endswith(ending.lower())):
        return input_str[:-len(ending)]
    return input_str
