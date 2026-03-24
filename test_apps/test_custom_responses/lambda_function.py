"""
Test app used in test app panel to test custom responses and validation.
"""

from __future__ import absolute_import
import json

class ErrorBehaviors:
    RAISE = 'raise' # Raise an error to simulate unhandled error
    RETURN = 'return' # Return an error response to simulate expected error

def app_handler(event, context):

    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    trigger_name = event.get('trigger_name')

    print(f'Call received for trigger_name: {trigger_name}')

    error_behavior = app_settings.get('error_behavior')
    if error_behavior == ErrorBehaviors.RAISE:
        raise RuntimeError('Raising error')
    if error_behavior == ErrorBehaviors.RETURN:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Expected error',
            })
        }

    custom_response = app_settings.get('custom_response') or {}

    full_response = {
        'statusCode': 200,
        'body': json.dumps(custom_response),
    }
    print(f'Returning response: {json.dumps(full_response)}')
    return full_response
