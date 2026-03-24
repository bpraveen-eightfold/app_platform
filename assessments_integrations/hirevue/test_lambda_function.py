from lambda_function import AssessmentAdapter

import glog as log

app_settings = {
   'base_url': 'https://eightfold.stghv.com/',
   'default_user': 'skumar@eightfold.ai',
   'api_key': '',
   'api_version': '1.2.0',
   'suppress_participants_email': True
}

ha = AssessmentAdapter(app_settings)
#import pdb
#pdb.set_trace()
resp = ha.get_logo_url()
log.info(resp)
resp = ha.is_webhook_supported()
log.info(resp)
ha.login()
webhook_settings = {'endpoint_url': "https://notifications.eightfold.ai/event/assessment/cf23788f349d40589106f803194c90d2/eightfolddemo-skumar.com/demo/Zf8lxcc1c9ShzdVTZdx74Yi65eT5K27uMTYxNjM5NjMyMGVpZ2h0Zm9sZGRlbW8tc2t1bWFyLmNvbWRlbW9jZjIzNzg4ZjM0OWQ0MDU4OTEwNmY4MDMxOTRjOTBkMg=="}
req_data = {'ef_settings': {'webhook_settings': webhook_settings}}
resp = ha.setup(req_data)
log.info(resp)
resp = ha.get_notification_urls()
log.info(resp)
tests = ha.list_tests({})
log.info(tests)
req_data = {
    'firstname': 'Satyajeet',
    'lastname': 'Kumar',
    'invite_metadata': {'email': 'satyajeet.kr.gupta+126@gmail.com', 'profile_id': 1359717, 'test_id': 2942089, 'pid': 2150986}
}

ic = ha.invite_candidate(req_data, True)
log.info(ic)
interview_id = ic.get('assessment_id')
req_data = {'test_id': 2942089,
            'assessment_id': interview_id}
r = ha.fetch_candidate_report(req_data)
log.info(r)
payload = {
    "eventType": "interviewFinished",
    "details": {
        "code": "Sa77k9n-5s77mg",
        "external_id": "214534",
        "isOpenvue": False,
        "interview_id": 44101873,
        "external_ids": [{"partner_type": "eightfold", "externalCandidateId": "{\"ats_job_id\": 1464143, \"application_id\": null, \"profile_id\": 214534, \"pid\": 1464143, \"ats_candidate_id\": null, \"test_id\": 2942089, \"email\": \"skumar@eightfold.ai\"}", "external_id": "214534"}],
        "type": "on-demand"
    }
}
req_data = {'headers': None,
            'request_payload': payload
           }
r = ha.process_webhook_request(req_data)
log.info(r)
ha.logout()
