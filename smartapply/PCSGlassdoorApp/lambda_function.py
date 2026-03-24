# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json
import jinja2
import requests


def smartapply_job_page_view_handler(event, context):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {}) 
    app_settings = event.get('app_settings', {})

    if trigger_name != 'smartapply_job_page_view':
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected trigger_name {}'.format(trigger_name)}),
        }

    try:
        site_embedding = app_settings.get('site-embedding','')
        
        """
        Add business logic here
        - Make API calls to remote systems -> Slack, Asana, Salesforce, Instagram, Youtube, etc.
        - Process and massage data for your return values
        - If your app is visual (like for career_hub_profile_view apps), and you want custom content, render your app here.  
        """
        data = {
            'title': 'Glassdoor Widget',
            'embed_htmls': site_embedding
        }
        html = jinja2.Template(open('template.html').read()).render(data=data)
    except Exception as e:
        error = 'Sorry, we are currently unable to connect to Glassdoor.'

        data = {
            'error': error,
            'title': 'Glassdoor Widget',
            'stacktrace': traceback.format_exc() or 'Internal Error',
        }
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data })
        }

    print(data)
    return {
        'statusCode': 200,
        'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800})
        }
