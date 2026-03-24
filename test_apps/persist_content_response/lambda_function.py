# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
This handle position_export and returns a file to persist in response
"""

from __future__ import absolute_import

import base64
import json
import os

def app_handler(event, context):
    trigger_name = event.get('trigger_name')
    print('Call received for trigger_name: {}'.format(trigger_name))

    if trigger_name != 'position_export':
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'unsupported trigger ' + trigger_name
            }),
        }

    # content_file is hardcoded and generate a fully qualified file path
    content_file_name = _get_content_file_name(event.get('app_settings', {}))
    content_file_path = '{current_file_dir}/data/{content_file_name}'.format(
        current_file_dir=os.path.dirname(os.path.realpath(__file__)),
        content_file_name=content_file_name
    )

    content_data, content_data_encoded = None, None
    with open(content_file_path, 'rb') as content_file:
        content_data = content_file.read()
        # Make sure that the type is str and not bytes
        content_data_encoded = base64.b64encode(content_data).decode('utf-8')

    data = {
        'actions': [{
            'action_name': 'persist_content',
            'request_data': {
                'content': [{
                    'data': content_data_encoded,
                    'identifier': content_file_name,
                    'encoding': 'base64'
                }]
            }
        }]
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }

def _get_content_file_name(app_settings):
    if not app_settings:
        return 'persist_content_data_small.xlsx'
    file_size = app_settings.get('file_size', 'small')
    if file_size == 'med':
        return 'persist_content_data_med.xlsx'
    elif file_size == 'small':
        return 'persist_content_data_small.xlsx'
    return 'persist_content_data_small.xlsx'
