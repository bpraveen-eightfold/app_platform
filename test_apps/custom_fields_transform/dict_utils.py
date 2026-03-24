from __future__ import absolute_import

import collections
from jsonpath_ng.ext import parse
import regex_utils

def safe_get(d, key, default=None):
    if not d:
        return default
    return d.get(key, default)

def lookup_jsonpath(data, expr, default=None):
    """NOTE: If you are going to make repeated calls to this method with same expr value,
    it's better to use the other method lookup_jsonpath_with_parsed_expr() for faster lookups
    on subsequent calls."""
    return (lookup_jsonpath_all(data, expr) or [default])[0]


def lookup_jsonpath_all(data, expr):
    return [match.value for match in jsonpath_parsed_expr(expr).find(data)] if expr else []

def jsonpath_parsed_expr(expr):
    return parse(expr)

def update_nested_val_from_expr(data, expr, value, delimiter='.'):
    if delimiter not in expr:
        if isinstance(data, list) and expr.isdigit():
            expr = int(expr)
        data[expr] = value
        return data
    key, expr = expr.split(delimiter, 1)
    match = regex_utils.search('(.*)\\[(\\d)]', key)
    if match and match.groups():
        # We land here if expr has the delimiter and the key is of the format ".*[INT].*"
        key, idx = match.groups()
        expr = '{}.{}'.format(idx, expr)
        if not safe_get(data, key):
            # We land here if data does not have the key. So, we initialize it to an empty list
            data.update({key: []})
    elif isinstance(data, list) and key.isdigit():
        # We land here if data is a list and expr has an int before delimiter
        from utils import str_utils ## Cyclic import, dict_utils uses str_utils
        key = str_utils.safe_get_int(key)
        while key >= len(data):
            # We append {} to ensure we do not run into out of bounds exception
            data.append({})
    elif not isinstance(data.get(key), (dict, collections.OrderedDict, list)):
        data[key] = {}
    data[key] = update_nested_val_from_expr(data[key], expr, value, delimiter=delimiter)
    return data
