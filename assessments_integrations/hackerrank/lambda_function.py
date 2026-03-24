import json
import traceback

from hackerrank_adapter import HackerRankAssessmentAdapter

def app_handler(event, context):
    app_settings = event.get('app_settings', {})

    req_data = event.get('request_data', {})
    trigger_name = req_data.get('trigger_name')

    print('Call recived for trigger_name: {}'.format(trigger_name))
    print('Request data is {}'.format(json.dumps(req_data)))
    data = None
    try:
        if trigger_name == 'assessment_get_logo_url':
            data = HackerRankAssessmentAdapter.get_logo_url()
        elif trigger_name == 'assessment_is_webhook_supported':
            data = HackerRankAssessmentAdapter.is_webhook_supported()
        elif trigger_name == 'assessment_list_tests':
            action_user_email = req_data.get('action_user_email')
            data = HackerRankAssessmentAdapter.list_tests(app_settings, action_user_email)
        elif trigger_name == 'assessment_invite_candidate':
            test_id = req_data.get('test_id')
            invite_metadata = req_data.get('invite_metadata')
            action_user_email = req_data.get('action_user_email')
            notification_url = req_data.get('notification_url')
            subject = app_settings.pop('email_subject', None)
            force_send = app_settings.pop('force_send', False)
            invite_valid_duration_days = app_settings.pop('invite_valid_duration_days', None)
            data = HackerRankAssessmentAdapter.invite_candidate(
                credentials=app_settings,
                test_id=test_id,
                subject=subject,
                invite_metadata=invite_metadata,
                action_user_email=action_user_email,
                notification_url=notification_url,
                force=force_send,
                invite_valid_duration_days=invite_valid_duration_days,
            )
        elif trigger_name == 'assessment_fetch_reports':
            test_id = req_data.get('test_id')
            action_user_email = req_data.get('action_user_email')
            data = list(HackerRankAssessmentAdapter.fetch_reports(app_settings, test_id, action_user_email))
        elif trigger_name == 'assessment_fetch_candidate_report':
            test_id = req_data.get('test_id')
            vendor_candidate_id = req_data.get('vendor_candidate_id')
            action_user_email = req_data.get('action_user_email')
            data = HackerRankAssessmentAdapter.fetch_candidate_report(app_settings, test_id, vendor_candidate_id, action_user_email)
        elif trigger_name == 'assessment_process_webhook':
            headers = req_data.get('headers')
            request_payload = req_data.get('request_payload')
            data = HackerRankAssessmentAdapter.process_webhook_request(headers, request_payload)
    except Exception as ex:
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
    print('Response is {}'.format(json.dumps(data)))
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
