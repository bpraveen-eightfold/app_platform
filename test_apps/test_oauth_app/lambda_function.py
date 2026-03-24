# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
This app check for existence of an oauth token
"""

from __future__ import absolute_import
import json

def app_handler(event, context):

    trigger_name = event.get('trigger_name')
    req_data = event.get('request_data', {})
    oauth_token = req_data.get('oauth_token')

    print(f'Call received for trigger_name: {trigger_name}')
    print(f'Found oauth token: {oauth_token}')

    return {
        'statusCode': 200,
        'body': json.dumps(
            {'data': {'oauth_token_found': oauth_token is not None}}
        )
    }
