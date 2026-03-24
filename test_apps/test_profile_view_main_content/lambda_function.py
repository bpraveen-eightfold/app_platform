# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
Test app for profile view main content apps
"""

from __future__ import absolute_import
import json

DUMMY_TEXT = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

def app_handler(event, context):

    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print('Call received for trigger_name: {}'.format(trigger_name))

    html = ''
    if trigger_name == 'ch_profile_view_main_content':
        if app_settings.get('raise_error_main'):
            raise RuntimeError('Raising error main view')
        html = '<p>Custom fields json: {}</p><p>{}</p>'.format(json.dumps(req_data.get('custom_fields')), DUMMY_TEXT)
    elif trigger_name == 'ch_profile_view_main_content_on_expand':
        if app_settings.get('raise_error_on_expand'):
            raise RuntimeError('Raising error on expand')
        html = '<p>Expanded html</p><p>{}</p>'.format(DUMMY_TEXT)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'html': html,
            'cache_ttl_seconds': 60,
        }),
    }
