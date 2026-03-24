import datetime
import math
import time
import traceback

import glog as log
import pytz
import six
from dateutil import parser as du

from utils import str_utils

MYSQL_TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
DATE_FORMATS = ('%Y-%m-%d', '%m/%d/%Y')
TIME_FORMATS = ('%H:%M:%S','%H:%M', '%H')
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
    log.warn(f"Failed to parse {date_str} in {date_formats} format")
    return None

def is_year_only(ts_or_ds):
    return (isinstance(ts_or_ds, (six.string_types)) and ts_or_ds.isdigit() or \
        isinstance(ts_or_ds, (int, float, six.integer_types)) and ts_or_ds >=0 and ts_or_ds < 3000) and len(str(ts_or_ds)) == 4

def to_datetime(ts_or_date_str, default=None, tz=None, init_first_day=False):
    if is_year_only(ts_or_date_str) and init_first_day:
        return datetime.datetime(int(ts_or_date_str), 1, 1, 0, 0)
    ts = to_timestamp(ts_or_date_str, default=default)
    if ts is None:
        return default
    if tz:
        if isinstance(tz, six.string_types):
            tz = pytz.timezone(tz)
        assert isinstance(tz, datetime.tzinfo)
        return datetime.datetime.fromtimestamp(ts, tz)
    else:
        return datetime.datetime.fromtimestamp(ts)

def mysql_timestamp(seconds_since_epoch):
    if isinstance(seconds_since_epoch, datetime.datetime):
        return seconds_since_epoch.strftime(MYSQL_TIMESTAMP_FORMAT)
    return datetime.datetime.fromtimestamp(seconds_since_epoch).strftime(MYSQL_TIMESTAMP_FORMAT)

def create_chunk_timestamp_interval(lower_bound_ts, upper_bound_ts, interval_hours=1):
    chunked_interval = []
    lower_bound_ts = str_utils.safe_get_int(lower_bound_ts)
    upper_bound_ts = str_utils.safe_get_int(upper_bound_ts)
    start_ts = lower_bound_ts
    while start_ts < upper_bound_ts:
        end_ts = min(upper_bound_ts, start_ts + 3600 * interval_hours)
        chunked_interval.append((start_ts, end_ts))
        start_ts = end_ts
    return chunked_interval

def get_now():
    return datetime.datetime.now()

def get_start_timestamp_of_today():
    current_time = datetime.datetime.now()
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return to_timestamp(today_start)

def parse_time_str_for_today(time_str, time_format=TIME_FORMATS):
    for time_fmt in TIME_FORMATS:
        try:
            time_only = datetime.datetime.strptime(time_str, time_fmt)
            current_time = get_now()
            return current_time.replace(hour=time_only.hour, minute=time_only.minute, second=time_only.second)
        except ValueError:
            pass
    log.warn(f"Failed to parse {time_str} in {time_format} format")
    return None
