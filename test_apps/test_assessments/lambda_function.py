import json

def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    req_data = event.get('request_data', {})
    trigger_name = req_data.get('trigger_name')
    print('Call recived for trigger_name: {}'.format(trigger_name))
    print('Request data is {}'.format(json.dumps(req_data)))
    data = None
    if trigger_name == 'assessment_get_logo_url':
        data = {'logo_url': 'https://res.cloudinary.com/crunchbase-production/image/upload/lqlkg85sw4sgmp2xvznh'}
    elif trigger_name == 'assessment_is_webhook_supported':
        data = {'is_webhook_supported': app_settings.get('is_webhook_supported', True)}
    elif trigger_name == 'assessment_list_tests':
        data = [{'id':'1','name':'test1','duration_minutes':60,'published':True},
            {'id': 'about-me', 'name': 'about me'}]
    elif trigger_name == 'assessment_invite_candidate':
        if req_data.get('invite_metadata', {}).get('email') == 'jeffreychen+20@eightfold.ai':
            raise RuntimeError('my runtime error')
        data = {
            'email': 'jeffreychen@eightfold.ai',
            'assessment_id': 123,
            'vendor_candidate_id': 234,
        }
    elif trigger_name == 'assessment_process_webhook':
        headers = req_data.get('headers')
        request_payload = req_data.get('request_payload')
        data = {
            'invite_metadata': request_payload.get('invite_metadata'),
            'assessment_report': request_payload.get('assessment_report'),
        }
    elif trigger_name == 'assessment_fetch_candidate_report':
        data = {
            'email': 'jeffreychen@eightfold.ai',
            'status': 'completed',
            'score': 43,
        }

    print('Response is {}'.format(data))
    return {'statusCode': 200, 'body': json.dumps({'data': data})}
