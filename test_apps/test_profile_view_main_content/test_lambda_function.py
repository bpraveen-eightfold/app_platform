import traceback

from lambda_function import app_handler

req_data = {
    'custom_fields': {
        'efcustom_text_job_code': 'abcd'
    },
}
event = {
    'app_settings': {},
    'request_data': req_data,
    'trigger_name': 'ch_profile_view_main_content'
}
resp = app_handler(event, {})
print(resp)

event = {
    'app_settings': {},
    'request_data': req_data,
    'trigger_name': 'ch_profile_view_main_content_on_expand'
}
resp = app_handler(event, {})
print(resp)

event = {
    'app_settings': {'raise_error_main': True},
    'request_data': req_data,
    'trigger_name': 'ch_profile_view_main_content'
}
try:
    resp = app_handler(event, {})
except:
    print('Expected error confirmed')
    print(traceback.format_exc())

event = {
    'app_settings': {'raise_error_on_expand': True},
    'request_data': req_data,
    'trigger_name': 'ch_profile_view_main_content_on_expand'
}
try:
    resp = app_handler(event, {})
except:
    print('Expected error confirmed')
    print(traceback.format_exc())
