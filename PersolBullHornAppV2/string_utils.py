'''
Code for string utils
'''
import datetime
import math
import six
import pytz
import re
from dateutil import parser as dateutil_parser

def is_int(s):
    try:
        return isinstance(s, six.integer_types) or int(s) or s == '0' or s == 0
    except:
        pass
    return False

def is_float(s):
    try:
        return isinstance(s, float) or float(s) or 0.0 == float(s)
    except:
        pass
    return False

def parse_datetime(input_str, now=None, assume_utc=True, default=None, fast=False, fuzzy=False):
    if not input_str:
        return default
    if isinstance(input_str, datetime.datetime):
        return input_str
    # hack to detect if it's a int timestamp
    if isinstance(input_str, (int, float, six.integer_types)) or ((is_int(input_str) or is_float(input_str)) and ((not math.isnan(float(input_str))) and ((int(float(input_str)) > 864000) or (int(float(input_str)) < 0)))):
        try:
            # handle millis
            num_digits = math.log10(abs(int(float(input_str))))
            ts = float(input_str)/1000.0 if num_digits > 12 else float(input_str)
            return datetime.datetime.fromtimestamp(ts)
        except:
            return None
    if any(input_str.lower().strip().startswith(w) for w in ['notknown', 'notapplicable']):
        return None
    if any(input_str.lower().strip().startswith(w) for w in ['present', 'now', 'current', 'o momento']):
        return datetime.datetime.now() if not now else now
    if input_str.find("'") != -1:
        input_str = re.sub(r" '([\d][\d])$", ' 20\\1', input_str.strip())
    if input_str.find(u"\u2013") != -1:
        input_str = input_str.replace(u" \u2013 ", "")
    input_strs = [input_str]
    if input_str.find('(') != -1:
        input_strs.append(re.sub(r'\([^)]+\)', '', input_str.strip()))
    if len(input_str) < 3:
        return default
    if not default:
        default = datetime.datetime(datetime.datetime.today().year, 1, 1)
    for i_str in input_strs:
        try:
            dt = dateutil_parser.parse(i_str, default=default, fuzzy=fuzzy)
            # if needed, convert to UTC
            return dt.astimezone(pytz.utc) if not assume_utc and dt.tzinfo else dt
        except:
            pass
        if not fast:
            # fallback to date parser which supports more formats include i18n dates
            try:
                import dateparser ## Use inline import instead of global (Modules uses 9MB in memory)
                dt = dateparser.parse(i_str, languages={'en', 'es', 'fr', 'de', 'pt', 'sv'})  # limit languages else it's very slow
                if dt:
                    if dt.year > default.year + 10 or dt.year < default.year - 100:
                        return None
                    return dt
            except:
                pass
    return None
