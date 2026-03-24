# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json
import requests
import jinja2

INSTAGRAM_OEMBED_ENDPOINT_URL = 'https://graph.facebook.com/v10.0/instagram_oembed/'
BASE_URL = "https://www.instagram.com/p/"

def _get_instagram_feed(post_url, token):
    resp = requests.get(
        url=INSTAGRAM_OEMBED_ENDPOINT_URL,
        params={
        'url': post_url,
        'access_token':token
        },
    )
    if resp.status_code==200:
        json_resp = json.loads(json.dumps(resp.json()))
        return json_resp.get('html',{})
    return None

def app_handler(event, context):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {}) 
    app_settings = event.get('app_settings', {})

    if trigger_name != 'smartapply_job_page_view':
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected trigger_name {}'.format(trigger_name)}),
        }

    try:
        app_id = app_settings.get('app-id','')
        client_token = app_settings.get('client-token','')
        token = app_id + "|" + client_token
        req_urls = app_settings.get('profile-ids',[])
        site_url = app_settings.get('site-url','')
        

        if len(req_urls) == 0:
            return {
            'statusCode': 200,
            'body': json.dumps({'data': {'error': 'Please enter Instagram Post IDS'}})
            }

        rendered_html = []
        for i in range(len(req_urls)):
            rendered_html.append((_get_instagram_feed(req_urls[i],token).replace('"',"'")))

        data = {
            'title': 'Recommended Instagram Posts',
            'embed_htmls': rendered_html
        }
        html = jinja2.Template(open('template.html').read()).render(data=data)
    except Exception as e:
        error = 'Sorry, we are currently unable to connect to Instagram.'

        data = {
            'error': error,
            'title': 'Recommended Instagram Posts',
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
