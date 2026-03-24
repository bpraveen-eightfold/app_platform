# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import
import os
import json
import jinja2
import traceback

def app_handler(event, context):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    
    if trigger_name != 'smartapply_job_page_view':
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected trigger_name {}'.format(trigger_name)}),
        }

    post_ids = app_settings.get('post_ids', [])

    try: 
        data = {
            'title': 'Recommended LinkedIn Posts',
            'post_ids': post_ids
        }

        html = jinja2.Template(open('template.html').read()).render(data=data)
    except Exception as e:
        error = 'Sorry, we are currently unable to connect to LinkedIn.'
        data = {
            'error': error,
            'title': 'Recommended LinkedIn Posts',
            'stacktrace': traceback.format_exc() or 'Internal Error',
        }

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data })
        }

    return {
            'statusCode': 200,
            'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800})
        }
        
