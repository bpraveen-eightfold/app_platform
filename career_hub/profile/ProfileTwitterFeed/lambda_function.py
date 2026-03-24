import json
import jinja2
import requests

DEFAULT_MAX_ITEMS = 3

def is_valid_source(app_settings, url):
    return 'twitter.com' in url

def get_twitter_feed_data(app_settings, profile_urls):
    if not profile_urls:
        return []
    ret = []
    count = 0
    for url in profile_urls:
        if count >= app_settings.get('max_items', DEFAULT_MAX_ITEMS):
            break
        if not is_valid_source(app_settings, url):
            continue
        # TODO: handle this better
        if 'publish.twitter.com/oembed' not in url:
            url = 'https://publish.twitter.com/oembed?url=' + url
        resp = requests.get(url)
        if resp.status_code == 200:
            json_data = resp.json()
            ret.append(json_data.get('html'))
            count = count + 1
    print('Twitter data {}'.format(ret))
    return ret

def career_hub_profile_view_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    profile_urls = req_data.get('profile_urls', [])

    data = {
        'title': app_settings.get('title', 'Twitter Feeds'),
        'limit': app_settings.get('max_items', DEFAULT_MAX_ITEMS)
    }

    try:
        data['items'] = get_twitter_feed_data(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing twitter URLs'
    
    html = jinja2.Template(open('template.html').read()).render(data=data)

    return {
        'statusCode': 200,
        'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800}),
    }

def ta_profile_view_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    profile_urls = req_data.get('profile_urls', [])
    data = {
        'title': app_settings.get('title', 'Twitter Feeds'),
        'limit': app_settings.get('max_items', DEFAULT_MAX_ITEMS)
    }
    
    try:
        data['items'] = get_twitter_feed_data(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing twitter URLs'
    
    html = jinja2.Template(open('template.html').read()).render(data=data)

    return {
        'statusCode': 200,
        'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800}),
    }

def app_handler(event, context):
    trigger_name = event.get('trigger_name')

    if trigger_name == 'career_hub_profile_view':
        return career_hub_profile_view_handler(event, context)
    if trigger_name == 'ta_profile_view':
        return ta_profile_view_handler(event, context)

    return {
        'statusCode': 500,
        'body': json.dumps({'error': 'Unexpected trigger_name {}'.format(trigger_name)}),
    }
