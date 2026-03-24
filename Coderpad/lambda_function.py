# pylint: disable=ef-restricted-imports, unused-variable, unused-import

from __future__ import absolute_import

import time
import json
import traceback
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def app_handler(event, context):
    if event.get('trigger_name') == 'interview_feedback_view'
        # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
        request_data = event.get('request_data', {})

        # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
        app_settings = event.get('app_settings', {})

        if not request_data.get('assessment_id'):
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'Please provide assessment_id in request_data'})
            }

        assessment_vendor = (request_data.get('assessment_vendor') or '').lower()
        if assessment_vendor != 'coderpad':
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'The vendor is not coderpad but is {}'.format(assessment_vendor)})
            }

        try:
            assessment_details = {}
            assessment_id = request_data.get('assessment_id').split('/')[-1]
            api_token = app_settings.get('api_token')
            assessment_url = 'https://app.coderpad.io/api/pads/{}'.format(assessment_id)
            headers = {
                'Authorization': 'Token token="{}"'.format(api_token)
            }
            resp = requests.get(assessment_url, headers=headers)
            resp.raise_for_status()
            resp_json = json.loads(resp.content)
            assessment_details = {
                'assessment_url': resp_json.get('url'),
                'assessment_feedback': resp_json.get('notes'),
                'assessment_vendor': 'coderpad',
                'title': resp_json.get('title'),
                'owner_email': resp_json.get('owner_email'),
                'participants': resp_json.get('participants'),
                'contents': resp_json.get('contents')
            }
            return {
                'statusCode': 200,
                'body': json.dumps({'assessment_details': assessment_details})
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
