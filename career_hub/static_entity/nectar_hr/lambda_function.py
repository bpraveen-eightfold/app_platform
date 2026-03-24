# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
Nectar HR app
"""

from __future__ import absolute_import
import json

def app_handler(event, context):
    trigger_name = event.get('trigger_name')

    print(f'Call received for trigger_name: {trigger_name}')

    app_url = None
    if trigger_name == 'careerhub_static_entity':
        app_url = 'https://app.nectarhr.com/'

        return {
            'statusCode': 200,
            'body': json.dumps({
                'app_url': app_url,
                'cache_ttl_seconds': 3600,
            }),
        }

    return {
        'statusCode': 500,
        'body': json.dumps({'error': f'Unexpected trigger_name {trigger_name}'}),
    }
