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
    if event.get('trigger_name') == 'pre_schedule_invite':
        # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
        request_data = event.get('request_data', {})

        # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
        app_settings = event.get('app_settings', {})

        assessment_vendor = (request_data.get('assessment_vendor') or '').lower()
        if assessment_vendor != 'coderpad':
            return {
                'statusCode': 200,
                'body': json.dumps({'error': 'The vendor is not coderpad but is {}'.format(assessment_vendor)})
            }

        try:
            candidate_name = request_data.get('candidate_name')
            interviewer_name = request_data.get('interviewer_name')
            interviewer_email = request_data.get('interviewer_email')
            data = {
                'title': '{}/{}'.format(candidate_name, interviewer_name),
                'language': 'python',
                'owner_email': interviewer_email
            }
            api_token = app_settings.get('api_token')
            headers = {
                'Authorization': 'Token token="{}"'.format(api_token)
            }
            if app_settings.get('test_mode'):
                resp_json = {
                    'url': 'https://app.coderpad.io/MW7TZRYA',
                    'title': 'Anurag/Demo',
                    'owner_email': 'anuragn@eightfold.ai'
                }
            else:
                resp = requests.post('https://app.coderpad.io/api/pads', headers=headers, data=data)
                resp.raise_for_status()
                resp_json = json.loads(resp.content)
            assessment_details = {
                'assessment_url': resp_json.get('url'),
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
