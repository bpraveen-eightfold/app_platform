import six
import math
import datetime
import time
import traceback

from dateutil import parser as du
import pytz

def listify(list_or_element):
    if isinstance(list_or_element, list):
        return list_or_element
    elif list_or_element is None:
        return []
    if isinstance(list_or_element, set):
        return list(list_or_element)
    if isinstance(list_or_element, odict_keys):
        return list(list_or_element)
    return [list_or_element]

def safe_get_float(s, default=0.0):
    try:
        return float(s)
    except:
        return default

def to_timestamp(dt, default=0):
    if isinstance(dt, (int, float, six.integer_types)) or safe_get_float(dt) > 864000:
        ts = float(dt)
        # handle millis
        if ts > 0 and math.log10(ts) > 12:
            return ts / 1000.0
        return ts
    if not dt:
        return default
    try:
        if isinstance(dt, (str, six.text_type)):
            dt = du.parse(dt)
        # if date has a timezone not the same as utc, then convert to utc
        if isinstance(dt, datetime.datetime) and dt.utcoffset() and dt.utcoffset().seconds:
            utc = pytz.timezone('UTC')
            dt = utc.normalize(dt.astimezone(utc))
        # NOTE: timetuple() does not include microsecond part of dt, so add it explicitly
        t = (time.mktime(dt.timetuple()) + (dt.microsecond/1000000. if getattr(dt, 'microsecond', None) else 0)) if dt else default
        return t
    except:
        print('Failed to convert to_timestamp %s, exception: %s', dt, traceback.format_exc())
        return default
