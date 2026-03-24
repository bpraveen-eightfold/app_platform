import json


def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        request_data = event.get('request_data')
        print("request data: ", request_data)
        username = request_data.get('email').replace('demo@','').replace('.com', '')
        data = {
                'title': 'Monday',
                'subtitle': username,
                'logo_url': 'https://static.vscdn.net/images/careers/demo/eightfolddemo-pborde-20201023/1649894443::monday-2.jpg',
                'action_button': {
                    'label': 'View',
                    'onClick': 'window.open("https://monday.com/")',
                },
                'tiles': [
                    {'header': 'This Month', 'value': 10},
                    {'header': 'Next Month', 'value': 15}
                ],
                'table': {
                    'headers': ['Title', 'Last Activity'],
                    'rows': [
                        [
                            {'value': 'task link', 'link': 'https://app.asana.com/0/home/1160225843515018'},
                            {'value': 'today'}
                            ]
                        ]
                }
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
        }
    