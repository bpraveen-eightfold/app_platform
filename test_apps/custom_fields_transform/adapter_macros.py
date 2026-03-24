''' Macros for adapter fetch and transform'''
from __future__ import absolute_import

import six
from collections import OrderedDict
import dict_utils

def extract_app_qna(ef_application_dict, question_id, default=None, question_id_suffixes=[]):
    if question_id is None:
        raise Exception('question_id cannot be None')
    if not ef_application_dict:
        return default
    qna = next((q for q in ef_application_dict['questions'] or [] if str(q['question_id']) == str(question_id)), None)
    def check_with_suffixes(qid):
        return any((True for suffix in question_id_suffixes or [] if str(qid) == str(question_id+suffix)))

    if not qna:
        qna = next((q for q in ef_application_dict['questions'] or [] if check_with_suffixes(q['question_id'])), None)
    return qna['answer'] if qna else default


def remap_value(raw_value, field_name, value_map):
    """---
    description: >
        This macro is used when we want to remap the value of certain existing field.
    title: Remap Value
    macro_name: adapter_macros.remap_value
    macro_type: transform
    properties:
        field_name:
            type: string
            description: field name whose value needs to be remapped.
            examples:
            - "gender"
        value_map:
            type: object
            title: List of Mappings
            propertyNames:
                type: string
                key_title: Map (From)
                value_title: Map (To)
            patternProperties:
                '':
                type: string
            description: >
                it will be a map of key: value pairs.
            examples:
            - "{'m': 'Male', 'f': 'Female'}"
    """
    if not field_name:
        raise Exception('field_name is a required field')
    if not value_map:
        raise Exception('value_map is a required field')
    if not isinstance(value_map, (dict, OrderedDict)):
        raise Exception('value_map must be a dict')

    field_name = field_name
    value_map = {k.lower(): v for k, v in six.iteritems(value_map)}
    if isinstance(raw_value, (dict, OrderedDict)):
        raw_val = raw_value.get(field_name, '').lower()
    return dict_utils.safe_get(value_map, raw_val, raw_val) if raw_val else None
