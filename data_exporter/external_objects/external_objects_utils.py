import os

import glog as log

from utils import json_utils


DATA_SCHEMA_VERSION_FILE_NAME = 'data_schema_version.json'

def get_data_schema_version(version):
    with open(os.path.join(os.path.dirname(__file__), DATA_SCHEMA_VERSION_FILE_NAME)) as f:
       data_schema_version = json_utils.load(f)
    return data_schema_version.get(version, {})

def filter_data_by_schema_version(data, tablename, version):
    schema = get_data_schema_version(version)
    field_list = schema.get(tablename, [])
    if not field_list:
        return data
    filtered_data = {field_name: data.get(field_name) for field_name in field_list}
    return filtered_data
