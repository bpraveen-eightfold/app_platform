from lambda_function import app_handler

req_data = {}
app_settings = {
    'wait_time': 10
}
event = {
    'app_settings': app_settings,
    'request_data': req_data,
    'trigger_name': 'position_export'
}
resp = app_handler(event, {})
print(resp)
