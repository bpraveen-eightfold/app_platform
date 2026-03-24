import json


LOGO_URL = 'https://blog.logomyway.com/wp-content/uploads/2021/08/zoom-icon.png'


def get_demo_data(username):
    data = {
        'title': 'Zoom',
        'subtitle': username,
        'logo_url': LOGO_URL,
        'action_button': {'label': 'Schedule', 'onClick': 'window.open("https://zoom.us/meeting/schedule")'},
        'tiles': [
            {'header': 'Personal Meeting URL', 'value': 'https://eightfold.zoom.us/j/5333930917'}
        ],
        'table': {
            'headers': ["Today's meetings", 'Starts at'],
            'rows': [
                [
                    {'value': 'Daily update meeting', 'link': 'https://eightfold.zoom.us/j/96771597172'},
                    {'value': '11:30 am'}
                ],
                [
                    {'value': 'Show & Tell', 'link': 'https://eightfold.zoom.us/j/98965451634?pwd=QlY4ZHBBUkVpTHpFeEdBbmE5OGZBZz09'},
                    {'value': '08:30 pm'}
                ],
            ]
        }
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 1})
    }


def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings', {})

        email = req_data.get('email', {})
        username = email.replace('demo@', '').replace('.com', '')
        is_demo_mode = app_settings.get('is_demo_mode')

        if is_demo_mode:
            return get_demo_data(username)
