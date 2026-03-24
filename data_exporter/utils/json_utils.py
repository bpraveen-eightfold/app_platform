import datetime
import json
from decimal import Decimal

from utils import str_utils

def _encoder(o):
    if isinstance(o, datetime.timedelta):
        return o.total_seconds()
    if isinstance(o, (datetime.datetime, datetime.date)):
        return o.isoformat()
    if isinstance(o, bytes):
        return str_utils.maybe_convert_bytes_to_str(o)
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, set):
        return list(o)
    return None

def dumps(o, **kwargs):
    # ujson is not that faster, use regular json
    # if a cls is explicitly passed in, continue with the default dumps
    if not kwargs.get('default') and not kwargs.get('cls'):
        # pylint:disable=ef-restricted-imports
        # pylint:disable=ef-restricted-method
        return json.dumps(o, default=_encoder, **kwargs)
    # pylint:disable=ef-restricted-imports
    # pylint:disable=ef-restricted-method
    return json.dumps(o, **kwargs)

def load(fp, **kwargs):
    return json.load(fp, **kwargs)
