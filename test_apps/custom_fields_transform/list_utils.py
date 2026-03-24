from __future__ import absolute_import

from collections import OrderedDict

odict_keys = type(OrderedDict().keys())
dict_keys = type(dict().keys())
dict_values = type(dict().values())
odict_values = type(OrderedDict().values())
dict_items = type(dict().items())
odict_items = type(OrderedDict().items())
from collections.abc import Generator

DICT_ITERABLE_TYPE = (odict_keys, dict_keys, dict_values, odict_values, dict_items, odict_items, Generator)

def listify(list_or_element):
    if isinstance(list_or_element, list):
        return list_or_element
    elif list_or_element is None:
        return []
    elif isinstance(list_or_element, (set,) + DICT_ITERABLE_TYPE):
        return list(list_or_element)
    return [list_or_element]


def flatten(l, key=None):
    if not l:
        return []
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], (list, tuple)):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i] if key is None else [x if isinstance(x, (list, tuple)) else key(x) for x in l[i]]
        i += 1
    return ltype(l)


# find first matching item (recursively) based on the key given a dict/list of dicts
def finditem(obj, key, default=None, allow_none=False, multiple=False, exclude_keys=()):
    if not obj:
        return default
    ret = []
    if isinstance(obj, (dict, OrderedDict)) and key in obj and key not in exclude_keys:
        #print 'returning %s' % obj[key]
        ret.append(obj[key] if obj[key] is not None or allow_none else default)
        if not multiple:
            return ret[0]
    if isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, OrderedDict, list)):
                #print 'recursing list'
                item = finditem(v, key, default=default, multiple=multiple, exclude_keys=exclude_keys)
                if item != default:
                    if not multiple:
                        return item
                    else:
                        ret += item
    else:
        for k, v in obj.items():
            if k in exclude_keys:
                continue
            if isinstance(v, (dict, OrderedDict, list)):
                item = finditem(v, key, default=default, multiple=multiple, exclude_keys=exclude_keys)
                if item != default:
                    if not multiple:
                        return item
                    else:
                        ret += item

    if not multiple:
        return ret[0] if ret else default
    return ret

def join(lst, join_char=',', default=None):
    if lst:
        stripped_lst = [x for x in lst if x and x.strip()]
        if stripped_lst:
            return join_char.join(stripped_lst)
    return default
