# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
Test app for checking attachment handling in email actions
"""
from __future__ import absolute_import

import os
import json
import base64


def app_handler(event, context):
    trigger_name = event.get('trigger_name')

    if trigger_name != 'position_export':
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'unsupported triger ' + trigger_name
            }),
        }

    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    # Hard coded file name 
    content_file_name = 'example-attachment.csv'
    content_file_path = '{current_file_dir}/data/{content_file_name}'.format(
        current_file_dir=os.path.dirname(os.path.realpath(__file__)),
        content_file_name=content_file_name
    )

    # Base64 encode the file data
    content_data, content_data_encoded = None, None
    with open(content_file_path, 'rb') as content_file:
        content_data = content_file.read()
        # Make sure that the type is str and not bytes
        content_data_encoded = base64.b64encode(content_data).decode('utf-8')

    if app_settings.get('is_email_with_template'):
        data = {
            'actions': [{
                'action_name': 'send_email_with_template_v2',
                'request_data': {
                    'emailTo': request_data.get('recruiter_email'),
                    'replyTo': request_data.get('recruiter_email'),
                    'emailFrom': request_data.get('recruiter_email'),
                    'templateCategory': 'contact',
                    'templateName': 'Outreach Template 1',
                    'attachments': [
                        {
                            'data': content_data_encoded,
                            'identifier': content_file_name,
                            'encoding': 'base64'
                        }
                    ]
                }
            }]
        }
    else:
        data = {
            'actions': [{
                'action_name': 'send_email',
                'request_data': {
                    'email_from': request_data.get('recruiter_email'), 
                    'email_to': request_data.get('recruiter_email'),
                    'subject': 'Test Email Attachments',
                    'body': 'Test email attachments',
                    'attachments': [
                        {
                            'data': content_data_encoded,
                            'identifier': content_file_name,
                            'encoding': 'base64'
                        }
                    ]
                }
            }]
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
