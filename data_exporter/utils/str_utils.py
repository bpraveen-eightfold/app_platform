import six

FALSY_VALUES = {'0', 'false', 'none', 'null', 'undefined', 'unknown'}
def maybe_convert_bytes_to_str(inp, ignore=False):
    if isinstance(inp, list) and inp and not six.PY2:
        return [maybe_convert_bytes_to_str(_i, ignore=ignore) for _i in inp]
    if inp is not None and not six.PY2 and isinstance(inp, bytes):
        return inp.decode('utf-8') if not ignore else inp.decode('utf-8', 'ignore')
    return inp

def is_truthy(str_val):
    if not str_val or (isinstance(str_val, six.string_types) and str_val.lower().strip() in FALSY_VALUES):
        return False
    return bool(str_val)

def safe_get_float(s, default=0.0):
    try:
        return float(s) if s not in ['nan', 'NaN'] else default
    except:
        return default

def safe_get_int(s, default=0):
    try:
        return int(s)
    except:
        return default

def safe_unicode_escape(input):
    try:
        return input.encode().decode('unicode_escape')
    except Exception:
        return input
