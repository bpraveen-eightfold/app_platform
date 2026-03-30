# pylint: disable=ef-restricted-imports, unused-variable, unused-import
"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import
import os
import json
import jinja2
import traceback
import requests

FACEBOOK_OEMBED_API_URL = 'https://graph.facebook.com/v10.0/oembed_post'

def _get_facebook_feed(post_url, token):

    resp = requests.get(
        url = FACEBOOK_OEMBED_API_URL,
        params = {
        'url': post_url,
        'access_token': token
        }
    )
    if resp.status_code == 200:
        json_resp = json.loads(json.dumps(resp.json()))
        return json_resp.get('html', {})

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

    post_urls = app_settings.get('post_urls')
    app_id = app_settings.get('app_id','')
    client_token = app_settings.get('client_token','')
    token = '{}|{}'.format(app_id, client_token)

    try:
        embed_htmls = []
        for post_url in post_urls:
            html_content = _get_facebook_feed(post_url, token)
            if not html_content:
                continue
            html_content = html_content.replace('"', '\'')
            html_content = html_content.replace("data-width='552'", "data-width='300'")
            embed_htmls.append(html_content)

        data = {
            'title': 'Recommended Facebook Posts',
            'embed_htmls': embed_htmls
        }

        html = jinja2.Template(open('template.html').read()).render(data=data)

    except Exception as e:
        error = 'Sorry, we are currently unable to connect to Facebook.'
        data = {
            'error': error,
            'title': 'Recommended Facebook Posts',
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
