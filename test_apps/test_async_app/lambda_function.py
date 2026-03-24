"""
Test async scheduled app.
BEFORE PACKAGING: Make sure ef_app_sdk.py is part of the package.
"""

from __future__ import absolute_import
import json
import time

from ef_app_sdk import EFAppSDK

def app_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    app_sdk = EFAppSDK(context)
    app_sdk.log(f'Call received for trigger_name: {trigger_name}')

    custom_response = app_settings.get('custom_response') or {}
    error_message = app_settings.get('error_message')
    sleep_time = int(app_settings.get('sleep_time') or 5)
    fetch_url = app_settings.get('fetch_url')

    app_sdk.log(f'Counting up to {sleep_time} seconds')
    for i in range(sleep_time):
        if i % 10 == 0 or i <= 60:
            app_sdk.log(i)
        time.sleep(1)

    if fetch_url:
        app_sdk.call_http_method('GET', url=fetch_url)

    if error_message:
        raise ValueError(error_message)

    full_response = {
        'statusCode': 200,
        'body': json.dumps(custom_response),
    }
    app_sdk.log(f'Returning response: {json.dumps(full_response)}')
    return full_response
