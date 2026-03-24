from lambda_function import app_handler

# TODO More robust testing

event = {
    'app_settings': {},
    'request_data': {u'headers': {}, u'trigger_name': u'assessment_process_webhook', u'request_payload': {u'invite_metadata': {u'ats_candidate_id': 50077, u'application_id': u'vs-50077-1125366-1617731463', u'profile_id': 50077, u'pid': 1125366, u'ats_job_id': 1125366, u'profile_enc_id': u'9K6d7aYj', u'test_id': 1, u'email': u'jeffreychen+4@eightfold.ai'}, u'assessment_report': {u'status': u'completed', u'profile_id': u'9K6d7aYj', u'pid': 1125366, u'score': 42, u'email': u'jeffreychen@eightfold.ai'}}}
}
x = app_handler(event, {})
print(x)
