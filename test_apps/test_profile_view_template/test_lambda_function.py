import traceback

from lambda_function import app_handler

req_data = {}
event = {
    'app_settings': {'show_error': False},
    'request_data': req_data,
    'trigger_name': 'career_hub_profile_view'
}
resp = app_handler(event, {})
print(resp)

event = {
    'app_settings': {'show_error': True},
    'request_data': req_data,
    'trigger_name': 'career_hub_profile_view'
}
resp = app_handler(event, {})
print(resp)
