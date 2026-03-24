from __future__ import absolute_import

import dict_utils
import list_utils
import str_utils

def extract_path_from_payload(payload, expr=None, default=None):
    """---
    description: >
        This function is used when we want to extract any nested path from the payload passed. Returns a single object found at the path.
    params:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        expr:
            type: string
            description: the string used for lookup
            examples:
                - 'custom_info.mentor_data'
        default:
            type: string
            description: the default result if no value is found for expression
            examples:
                - "No"
    """
    expr = expr or '[*]'
    response = dict_utils.lookup_jsonpath(payload, expr)
    return response or default

def extract_path_all(payload, expr):
    """---
    description: >
        This functions is used when we want to extract any nested path. This will return a list of multiple objects which match the path
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        expr:
            type: string
            description: the string used for lookup
            examples:
                - "custom_info.mentor_data"
    """
    expr = expr or '[*]'
    response = list_utils.flatten(dict_utils.lookup_jsonpath_all(payload, expr))
    return response if response != [None] else []

def pack_path_all(payload, expr):
    """---
    description: >
        This function is used when we want to add parent dictionaries to a list of dictionaries.
        example, when we have a list of dictionaries as [dict1, dict2],
        using expr as 'path1.path2' will convert orignal list to [{path1: {path2: {dict1}}}, {path1: {path2: {dict2}}}]
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        expr:
            type: string
            description: the name of dict(s) which will be added as a parent dict, to every dict in the list.
            examples:
                - "e:JobInformation.e:JobInformationGroup"
    """
    expr = expr or ''
    if not expr:
        return list_utils.flatten(payload)
    response = list_utils.flatten(
        [dict_utils.update_nested_val_from_expr(dict(), expr, obj) for obj in payload])
    return response if response != [None] else []

def extract_path_and_match(payload, expr, expected_result):
    """---
    description: >
        This function is used when we want to verify the result at a given path. We give two inputs, the path of
        the element to be extracted and the expected_value at the path.
        Returns true if the value at path matches with the expected_result, else returns False
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        expr:
            type: string
            description: the string used for lookup
            examples:
                - "custom_info.mentor_data"
        expected_result:
            type: string
            description: the expected result for value at path
            examples:
                - "True"
    """
    expr = expr or '[*]'
    response = dict_utils.lookup_jsonpath(payload, expr)
    return expected_result == response

def extract_path_all_and_match(payload, expr, expected_result):
    """---
    description: >
        This function is used when we want to verify the result at a given path for all elements in a list. We give two inputs, the path of
        the element to be extracted and the expected_value at the path.
        Returns a list of flags which is of the same size as the input list - true if the value at path matches with the expected_result, else False
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        expr:
            type: string
            description: the string used for lookup
            examples:
                - "custom_info.mentor_data"
        expected_result:
            type: string
            description: the expected result for value at path
            examples:
                - "FALSE"
    """
    expr = expr or '[*]'
    response = dict_utils.lookup_jsonpath_all(payload, expr)
    return [expected_result == resp for resp in response]

def extract_and_transform_from_entity(payload, field, data_type, default=None):
    """---
    description: >
        This function is used when we want to find the result at a given path and fallback to a safe default
        with necessary type checks to make sure wrong data does not enter the system.
        We give three inputs - the path of the element to be extracted, a default value and the data type of extracted value
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        field:
            type: string
            description: the string used for lookup
            examples:
                - "custom_info.mentor_option"
        data_type:
            type: string
            description: the data_type of expected value at path
            default: string
            enum:
                - "string"
                - "int"
                - "bool"
                - "date"
                - "datetime"
                - "float"
            enumNames:
                - "String"
                - "Integer"
                - "Boolean"
                - "Date"
                - "Datetime"
                - "Float"
        default:
            title: Default
            type: string
            description: the default result if no value is found for expression
            examples:
                - "No"
    """
    if not payload or not field:
        raise Exception('Missing extraction field or payload')

    data_type = data_type or 'string'
    if data_type not in ('string', 'int', 'bool', 'date', 'datetime', 'float'):
        raise Exception('Unknown data type specified {}'.format(data_type))

    value = list_utils.finditem(payload, field)
    return str_utils.convert_to_data_type(data_type, value) or default

def extract_and_format_from_entity(payload, fields, data_paths, separator='     - '):
    """---
    description: >
        This function is used when we want to extract data for a given path
        from multiple entities and combine them using a separator
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        fields:
            type: array
            description: a list of simple string used for lookup. use this if the path to be extracted is a top level field.
            items:
                type: string
        data_paths:
            type: array
            description: a list of strings used for lookup. use this for nested checks
            items:
                type: string
        separator:
            type: string
            description: a separator used between the extracted values.
            default: "  - "
    """
    if not payload or not (fields or data_paths):
        raise Exception('Missing extraction field or payload')

    fields = fields or []
    if fields:
        vals = [list_utils.finditem(payload, field) for field in fields]
    else:
        data_paths = data_paths or []
        vals = [dict_utils.lookup_jsonpath(payload, data_path) for data_path in data_paths]

    return separator.join([v for v in vals if v]) if (any(vals) and separator) else None

def extract_from_multiple_paths(payload, data_paths, default=None):
    """---
    description: >
        This function is used when we want to find the first result at a given path from multiple possible matches.
        We can also fallback to a default, if needed.
    parameters:
        payload:
            type: dict
            description: the 'object' a value will be extracted from
            examples:
                - {'custom_info': {'mentor_data': 'some_value'}}
        data_paths:
            type: array
            description: a list of strings used for lookup
            items:
                type: string
        default:
            type: string
            description: the default result if no value is found for expression
            examples:
                - "No"
    """
    if not payload or not data_paths:
        raise Exception('Missing extraction field or payload')

    data_paths = data_paths or []
    val = [dict_utils.lookup_jsonpath(payload, data_path) for data_path in data_paths]
    val = [v for v in val if v]

    return val[0] if val else default

def group_list_by_field_path(entity_list, key_field_path, value_field_path, grouped_field_path):
    """
    description: >
        This function is used to group the values in the list with respect to the value of a specified field.
        This key_field_path value acts as the key and all the value_field_path values will be captured as a list.
    parameters:
        key_field_path:
            type: string
            description: Field path whose value should act as a key during grouping.
        value_field_path:
            type: string
            description: Field path whose value would be captured in the output object as a list.
        grouped_field_path:
            type: string
            description: Field path where grouped values would be set in the object.
    """
    if not entity_list or not key_field_path or not value_field_path or not grouped_field_path:
        raise Exception('Empty entity list or missing key or values field paths or missing target field path')
    
    entity_list = list_utils.listify(entity_list)

    grouped_dict = {}
    for entity in entity_list:
        key = dict_utils.lookup_jsonpath(entity, key_field_path)
        if not key:
            continue
        if key not in grouped_dict:
            grouped_dict[key] = []

        entity_value = dict_utils.lookup_jsonpath(entity, value_field_path)
        grouped_dict[key].append(entity_value)

    grouped_list = []
    for key, value in grouped_dict.items():
        grouped_item = {}
        dict_utils.update_nested_val_from_expr(grouped_item, key_field_path, key)
        dict_utils.update_nested_val_from_expr(grouped_item, grouped_field_path, value)
        grouped_list.append(grouped_item)
    return grouped_list
