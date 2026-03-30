# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json

import urllib.request as libreq
import feedparser
from datetime import datetime

BASE_API_URL = "http://export.arxiv.org/api/query?search_query=all:"
ARXIV_LOGO_URL = "https://static.vscdn.net/images/career_hub/profile/arXiv.png"
NUM_RECORDS = 100

def get_timestamp(time):
    return datetime.strptime(time,'%Y-%m-%dT%H:%M:%SZ').strftime("%d %B, %Y")
def get_arxiv_data(username):
    full_name = username.replace(" ", "+")
    with libreq.urlopen('http://export.arxiv.org/api/query?search_query=all:%22' + full_name + '%22&max_results='+str(NUM_RECORDS)+"&sortBy=lastUpdatedDate") as url:
        response = url.read()
    feed = feedparser.parse(response)
    rows = []
    num_papers = 0
    for entry in feed.entries:
        num_papers += 1
        rows.append([{'value': entry.title, 'link': entry.id},{'value':get_timestamp(entry.updated)}])

    return rows[:3],num_papers

def app_handler(event, context):
    # Extract request_data -> this is the dynamic, per-invocation data for your app. E.g. profile info, message to be sent, etc.
    request_data = event.get('request_data', {})

    # Extract app_settings -> this are the static params for your app configured for each unique installation. E.g. API keys, allow/deny lists, etc.
    app_settings = event.get('app_settings', {})
    fullname_swap_map = app_settings.get('fullname_swap_map', {})

    full_name = request_data.get("fullname")
    full_name = fullname_swap_map.get(full_name) or full_name
    if not full_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Please provide full name in request_data'}),
        }
    rows, num_papers = get_arxiv_data (full_name)

    if not rows:
        data = {'title': 'ArXiv',
            'logo_url': ARXIV_LOGO_URL}
        data['error'] = 'arxiv user not found for {}'.format(full_name)
    else:
        try:
            data = {
                'title': 'ArXiv',
                'subtitle': full_name,
                'logo_url': ARXIV_LOGO_URL,
                'action_button': {
                    'label': 'View',
                    'onClick': 'window.open("https://arxiv.org/search/?query=%22{0}%22&searchtype=all")'.format(full_name.replace(" ","+")),
                },
                'tiles': [{'header': 'Publications', 'value': num_papers}],
                'table': {
                    'headers': ['Recent Publications', 'Date'],
                    'rows': rows
                }
            }
        except Exception as ex:
            print(str(ex))
            return {
                'statusCode': 400,
                'body': json.dumps({'error': str(ex) or 'Internal Error'}),
            }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data,'cache_ttl_seconds': 10})
    }
