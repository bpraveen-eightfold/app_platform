import os
import json
import requests
from hashids import Hashids

# TODO -> removed profile hash. Thread through profile_id

API_ENDPOINT = 'https://{domain}.eightfold.ai/internal/api/get_suggested_employees?profile_id={pr_id}&pid={pid}&count={cnt}'
APP_TEMPLATE = 'profile/ef_smart_scheduler_template.html'

def app_handler(event, context):
    if event.get('trigger_name') == 'ta_profile_view':

        # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
        request_data = event.get('request_data', {})
        print('request_data: {}'.format(request_data))

        # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
        app_settings = event.get('app_settings', {})
        print('app_settings: {}'.format(app_settings))

        domain = app_settings.get('domain')
        api_key = app_settings.get('access_token')

        enc_id = request_data['profile_url'].split('/')[-1]
        pr_id = PROFILE_HASHIDS.decode(enc_id)[0]
        pid = request_data.get('pid')
        print('Processing for pr_enc_id: {} pr_id: {} pid: {}'.format(enc_id, pr_id, pid))

        url = API_ENDPOINT.format(
            domain=domain,
            pr_id=pr_id,
            pid=pid,
            cnt=app_settings.get('num_results', 5))

        r = requests.get(url, auth=(api_key, ''), timeout=60)
        if r.status_code != 200:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': '/api/get_suggested_employees error'}),
            }

        resp = r.json()
        print('/api/get_suggested_employees resp: {}'.format(resp))

        # If returning custom rendered html, please return it mapped to key 'html'
        return {
            'statusCode': 200,
            'body': json.dumps({'data': resp, 'template': APP_TEMPLATE})
        }
