import json


def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_home_sidebar_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings', {})

        data = {
            'title': '1234',
            'subtitle': 'something here',
            'logo_url': 'https://static.vscdn.net/images/logos/eightfold_logo_no_text.svg',
        }
        return {
            'statusCode': 200,
            'body': json.dumps({'data':data})
        }
        
        
