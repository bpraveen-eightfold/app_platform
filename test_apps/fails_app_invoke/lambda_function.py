# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
This app fails on every invocation i.e. is only useful for testing error scenarios
"""

from __future__ import absolute_import
import json
import traceback

def app_handler(event, context):

    req_data = event.get('request_data', {})
    trigger_name = req_data.get('trigger_name')

    print('Call received for trigger_name: {}'.format(trigger_name))

    try:
        raise Exception('Testing failure path')
    except Exception as ex:
        stacktrace = traceback.format_exc()
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), stacktrace)
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': stacktrace,
            }),
        }
