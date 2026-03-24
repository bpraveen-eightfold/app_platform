from __future__ import absolute_import

import six
import math
import str_utils
from dateutil import parser as du
import datetime
import pytz
import time
import glog as log
import traceback

DATE_FORMATS = ('%Y-%m-%d', '%m/%d/%Y')

# pylint:disable=redefined-outer-name
def to_timestamp(dt, default=0):
    if isinstance(dt, (int, float, six.integer_types)) or str_utils.safe_get_float(dt) > 864000:
        ts = float(dt)
        # handle millis
        if ts > 0 and math.log10(ts) > 12:
            return ts / 1000.0
        return ts
    if not dt:
        return default
    try:
        if isinstance(dt, (six.string_types)):
            dt = du.parse(dt)
        # if date has a timezone not the same as utc, then convert to utc
        if isinstance(dt, datetime.datetime) and dt.utcoffset() and dt.utcoffset().seconds:
            utc = pytz.timezone('UTC')
            dt = utc.normalize(dt.astimezone(utc))
        # NOTE: timetuple() does not include microsecond part of dt, so add it explicitly
        t = (time.mktime(dt.timetuple()) + (dt.microsecond/1000000. if getattr(dt, 'microsecond', None) else 0)) if dt else default
        return t
    except:
        log.error('Failed to convert to_timestamp %s, exception: %s', dt, traceback.format_exc())
        return default

def date_obj_from_str(date_str, date_formats=DATE_FORMATS):
    """Returns a datetime object from given date string."""
    if not date_str:
        return None
    for date_fmt in date_formats:
        try:
            return datetime.datetime.strptime(date_str, date_fmt)
        except ValueError:
            pass
    log.warn("Failed to parse %s in %s format" % (date_str, date_formats))
    return None

def date_obj_from_seconds(seconds, timezone_offset_minutes=None, raise_error=True):
    """Returns a datetime object from seconds signifying the time passed since epoch."""
    try:
        if not seconds:
            return None
        if timezone_offset_minutes:
            seconds = seconds + (timezone_offset_minutes * 60)
        return datetime.datetime.fromtimestamp(int(seconds))
    except:
        log.warn('Error while converting seconds {} to dt. timezone_offset_minutes: {}, raise_error: {}'.format(seconds, timezone_offset_minutes, raise_error))
        if raise_error:
            raise
    return None

def date_to_str(date_obj, date_fmt='%Y-%m-%d', dayfirst=False):
    """Returns a string representation for given date object."""
    if not date_obj:
        return None
    kwargs = {
        'dayfirst': dayfirst
    }
    if isinstance(date_obj, six.string_types):
        date_obj = du.parse(date_obj, **kwargs)
    return date_obj.strftime(date_fmt)

def timestamp_to_str(ts, date_fmt='%Y-%m-%d'):
    """Returns a string representation for given timestamp."""
    return date_to_str(date_obj_from_seconds(ts), date_fmt)

def timestamp(seconds_ago=0, ndigits=0):
    if ndigits == 0:
        return int(time.time() - seconds_ago)
    return round(time.time() - seconds_ago, ndigits)
