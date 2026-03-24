# pylint: disable=ef-restricted-imports, unused-variable, unused-import

from __future__ import absolute_import

import time
import json
import traceback
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def app_handler(event, context):
    # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
    request_data = event.get('request_data', {})

    # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
    app_settings = event.get('app_settings', {})

    if not request_data.get('profile_json_list'):
        return {
            'statusCode': 200,
            'body': json.dumps({'error': 'Please provide profile_json_list in request_data'})
        }

    try:
        user_email = request_data['user_email']
        data = {'actions': []}
        action = {
            'action_name': 'download_to_pdf',
            'request_data': {
                'profile_id_list': [pr_json.get('id') for pr_json in request_data.get('profile_json_list')],
                'add_resume': app_settings.get('add_resume'),
                'mask_profiles': app_settings.get('mask_profiles')
            }
        }
        data['actions'].append(action)
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data})
        }
    except Exception as ex:
        logging.info(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
