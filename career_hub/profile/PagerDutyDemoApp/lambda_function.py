import json


LOGO_URL = "https://assets.website-files.com/5fd148f419b866c77225d463/617c599796f240911ffc46c3_pagerduty-logo.png"


def return_error_template():
    data = {
        'title': 'PagerDuty',
        'error': 'Unable to fetch data',
        'logo_url': LOGO_URL
    }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
    }


def get_tiles_data():
    tiles = [
        {'header': 'Assigned Tasks',    'value': 0},
        {'header': 'Urgent Alerts',     'value': 2}
    ]

    return tiles


def get_table_data():
    headers = ['Tasks & Alerts', 'Created on']

    rows = []
    rows.append([
        {'value': 'App Platform Too Many Action Errors', 'link': 'https://volkscience.pagerduty.com/incidents/Q2DR3001IORF14'},
        {'value': 'Apr 7, 2022 at 14:44'}
    ])

    rows.append([
        {'value': 'App Platform Error Rate-Net Error Rate', 'link': 'https://volkscience.pagerduty.com/incidents/Q1BOBXSQDHOU9V'},
        {'value': 'Apr 19, 2022 at 10:00'}
    ])

    table = {
        'headers': headers,
        'rows': rows
    }

    return table


def get_action_button_data():
    action_button = {'label': 'Home', 'onClick': 'window.open("https://www.pagerduty.com/")'}

    return action_button


def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings', {})

        email = req_data.get('email', {})
        username = email.replace('demo@', '').replace('.com', '')
        fullname = req_data.get('fullname', {})
        location = ''

        enable_location = app_settings.get('enable_location', True)
        if enable_location:
            location = req_data.get('location', {})

        action_button = get_action_button_data()

        try:
            tiles = get_tiles_data()
            table = get_table_data()

            data = {
                'title': f'PagerDuty ({fullname})',
                'subtitle': username,
                'logo_url': LOGO_URL,
                'action_button': action_button,
                'tiles': tiles,
                'table': table,
                'footer': location
            }

            return {
                'statusCode': 200,
                'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
            }

        except:
            return return_error_template()
