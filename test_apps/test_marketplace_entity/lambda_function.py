# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
Test app for marketplace entity apps
"""

from __future__ import absolute_import
import json

DUMMY_TEXT = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print('Call received for trigger_name: {}'.format(trigger_name))

    app_html = None
    app_url = None
    if trigger_name == 'careerhub_static_entity':
        # mode can be 'html' or 'url'
        mode = app_settings.get('mode', 'html')
        if mode == 'html':
            app_html = '<p>{}</p>'.format(DUMMY_TEXT)
        elif mode == 'url':
            app_url = app_settings.get('app_url', 'https://eightfold.ai')

    return {
        'statusCode': 200,
        'body': json.dumps({
            'app_html': app_html,
            'app_url': app_url,
            'cache_ttl_seconds': 60,
        }),
    }
