# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
Test app for profile view apps using all template fields
"""

from __future__ import absolute_import
import json

def app_handler(event, context):

    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print(f'Call received for trigger_name: {trigger_name}')

    data = {
        'title': 'Title Text',
        'subtitle': 'Subtitle Text',
        'logo_url': 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg',
        'tiles': [
            {
                'header': 'Tile Header 1',
                'value': 'Tile Value 1'
            },
            {
                'header': 'Tile Header 2',
                'value': 'Tile Value 2'
            }
        ],
        'table': {
            'headers': [
                'Table Header 1',
                'Table Header 2'
            ],
            'rows': [
                [
                    {
                        'value': '1,1'
                    },
                    {
                        'value': '1,2',
                        'link': 'https://app.eightfold.ai'
                    }
                ]
            ]
        },
        'footer': 'Footer Text'
    }

    if app_settings.get('show_error'):
        data = {
            'title': 'Title Text',
            'subtitle': 'Subtitle Text',
            'logo_url': 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg',
            'error': 'Error Message',
        }
    return {
        'statusCode': 200,
        'body': json.dumps({
            'data': data,
            'cache_ttl_seconds': 60,
        }),
    }
