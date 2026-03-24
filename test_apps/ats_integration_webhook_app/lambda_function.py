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

    req_payload = req_data.get('request_payload', {})
    if req_payload.get('entity_type') not in ['candidate', 'position']:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'unsupported entity_type' + (req_payload.get('entity_type') or '')
            }),
        }

    data = {
        'is_success': True,
        'actions': [{
            'action_name': 'ats_entity_create_update_action',
            'request_data': {
                'entity_type': req_payload['entity_type'],
                'entity_id': req_payload['entity_id'],
                'entity_payload': req_payload.get('entity_payload', {})
            }
        }]
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
