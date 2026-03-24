import datetime
import json
import requests
import jinja2

DEFAULT_MAX_ITEMS = 3
RSS_API_URL = 'https://api.rss2json.com/v1/api.json?rss_url='

def is_valid_source(app_settings, url):
    return 'medium.com/feed' in url

def get_medium_feed_data(app_settings, profile_urls):
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
        if 'rss_url' not in url:
            url = RSS_API_URL + url
        resp = requests.get(url)
        if resp.status_code == 200:
            json_data = resp.json()
            metadata = json_data.get('feed', {})
            feed = json_data.get('items', [])
            for f in feed:
                ret.append({
                    'title': f.get('title'),
                    'link': f.get('link'),
                    'date': datetime.datetime.strptime(f.get('pubDate'), '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y'),
                    'thumbnail': f.get('thumbnail')
                })
                count = count + 1
    print('Medium data {}'.format(ret))
    return ret


def career_hub_profile_view_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    profile_urls = req_data.get('profile_urls', [])
    data = {
        'title': app_settings.get('title', 'Medium Feeds'),
        'limit': app_settings.get('max_items', DEFAULT_MAX_ITEMS)
    }
    
    try:
        data['items'] = get_medium_feed_data(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing Medium URLs'
    
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
        'title': app_settings.get('title', 'Medium Feeds'),
        'limit': app_settings.get('max_items', DEFAULT_MAX_ITEMS)
    }
    
    try:
        data['items'] = get_medium_feed_data(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing Medium URLs'
    
    html = jinja2.Template(open('template.html').read()).render(data=data)

    return {
        'statusCode': 200,
        'body': json.dumps({'html': html, 'cache_ttl_seconds': 1800}),
    }


def app_handler(event, context):
    trigger_name = event.get('trigger_name')

    if trigger_name == 'career_hub_profile_view':
        return career_hub_profile_view_handler(event, context)
    elif trigger_name == 'ta_profile_view':
        return ta_profile_view_handler(event, context)

    return {
        'statusCode': 500,
        'body': json.dumps({'error': 'Unexpected trigger_name {}'.format(trigger_name)}),
    }

