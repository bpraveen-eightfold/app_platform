import json
import jinja2
import requests
import urllib.parse as urlparse
from urllib.parse import parse_qs

DEFAULT_MAX_VIDEOS = 3
YOUTUBE_EMBED_URL = 'https://www.youtube.com/embed/'

def is_valid_source(app_settings, url):
    sources = app_settings.get('sources', ['youtube.com', 'player.vimeo.com'])
    isValid = False
    for source in sources:
        if source in url:
            isValid = True
            break
    return isValid

def get_embeddable_url(url):
    ret = url
    if 'youtube.com' in url and 'embed' not in url:
        parsed = urlparse.urlparse(url)
        q = parse_qs(parsed.query)
        youtube_video_ids = q['v']
        if len(youtube_video_ids) > 0:
            ret = YOUTUBE_EMBED_URL + youtube_video_ids[0]
    return ret

def get_video_urls(app_settings, profile_urls):
    if not profile_urls:
        return []
    return [get_embeddable_url(u) for u in profile_urls if is_valid_source(app_settings, u)]

def career_hub_profile_view_handler(event, context):
    req_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})
    profile_urls = req_data.get('profile_urls', [])
    
    data = {
        'title': app_settings.get('title', 'Video Gallery'),
        'limit': app_settings.get('max_videos', DEFAULT_MAX_VIDEOS)
    }
    try:
        data['urls'] = get_video_urls(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing video URLs'

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
        'title': app_settings.get('title', 'Video Gallery'),
        'limit': app_settings.get('max_videos', DEFAULT_MAX_VIDEOS)
    }
    try:
        data['urls'] = get_video_urls(app_settings, profile_urls)
    except Exception as ex:
        data['error'] = 'Error while parsing YouTube URLs'

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
