# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependancies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import json
import traceback
import jinja2
import requests

BASE_TWITTER_API_URL = 'https://api.twitter.com/2/users/'

def _create_headers(bearer_token):
    headers = {'Authorization': 'Bearer {}'.format(bearer_token)}
    return headers

def _get_embed_url(user_id, tweet_id, tweet_url=None):
    if tweet_url:
        return 'https://publish.twitter.com/oembed?url={}'.format(tweet_url)

    return 'https://publish.twitter.com/oembed?url=https://twitter.com/{}/status/{}'.format(user_id, tweet_id)

def _get_response(url, headers=None, params=None):
    response = requests.request('GET', url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(
            'Request returned an error: {} {}'.format(
                response.status_code, response.text
            )
        )
    return response.json()

def _get_id_from_twitter_handle(headers, twitter_handle):
    
    url = BASE_TWITTER_API_URL + 'by?usernames={}'.format(twitter_handle)
    response = _get_response(url, headers=headers)

    twitter_id = None
    if response.get('data'):
        twitter_id = response.get('data')[0]['id'] 
    
    return twitter_id

def _fetch_tweet_ids(bearer_token, user_id):

    headers = _create_headers(bearer_token)
    twitter_id = _get_id_from_twitter_handle(headers, user_id)
    url = BASE_TWITTER_API_URL + '{}/tweets'.format(twitter_id)
    response = _get_response(url, headers)

    tweet_ids = []
    if response.get('data'):
        for item in response.get('data'):
            tweet_ids.append(item['id'])
    
    return tweet_ids

def app_handler(event, context):
    trigger_name = event.get('trigger_name', {})
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    if trigger_name != 'smartapply_job_page_view':
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Unexpected trigger_name: {}'.format(trigger_name)}),
        }

    try:
        tweet_urls = app_settings.get('tweet_urls')
        
        #if tweet urls are not provided - fetch the 10 most recent tweets using user_id and access_token
        urls = []
        if not tweet_urls:
            bearer_token = app_settings.get('token')
            user_id = app_settings.get('user_id')

            if not user_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Please provide user_id in app_settings'}),
                }

            if not bearer_token:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'Please provide access token in app_settings'}),
                }

            tweet_ids = _fetch_tweet_ids(bearer_token, user_id)
            for tweet_id in tweet_ids:
                urls.append(_get_embed_url(user_id, tweet_id))
        else:
            for tweet_url in tweet_urls:
                urls.append((_get_embed_url(user_id=None, tweet_id=None, tweet_url=tweet_url)))

        embed_htmls = []
        for url in urls:
            json_response = _get_response(url)
            if not json_response.get('html'):
                continue
            html_content = json_response.get('html').replace('"', '\'')
            embed_htmls.append(html_content)

        data = {
            'title': 'Recommended Tweets',
            'embed_htmls': embed_htmls
        }

        html = jinja2.Template(open('template.html').read()).render(data=data)

    except Exception as e:
        error = 'Sorry, we are currently unable to connect to Twitter.'
        data = {
            'error': error,
            'title': 'Recommended Tweets',
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
