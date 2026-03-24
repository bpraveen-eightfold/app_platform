# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
This app handles webhook_receive_event and responds with an echo action
"""

from __future__ import absolute_import
import json

def app_handler(event, context):

    req_data = event.get('request_data', {})
    trigger_name = req_data.get('trigger_name')

    print('Call received for trigger_name: {}'.format(trigger_name))

    if trigger_name != 'webhook_receive_event':
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'unsupported trigger ' + trigger_name
            }),
        }

    data = {
        'is_success': True,
        'actions': [{
            'action_name': 'echo',
            'request_data': {
                'echo_str': 'Echo from webhook_receive_event test app'
            }
        }]
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
