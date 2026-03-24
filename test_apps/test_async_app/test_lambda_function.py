from lambda_function import app_handler

event = {
    'request_data': {},
    'app_settings': {
        'sleep_time': 5,
        'fetch_url': 'https://app.eightfold.ai',
        'custom_response': {'data': {'actions': []}},
    },
    'trigger_name': 'scheduled_hourly'
}

class DummyContext:
    def __init__(self):
        self.aws_request_id = 'abc'

dummy_context = DummyContext()
app_handler(event, dummy_context)

event = {
    'request_data': {},
    'app_settings': {
        'sleep_time': 2,
        'fetch_url': 'https://app.eightfold.ai',
        'error_message': 'asdf',
    },
    'trigger_name': 'scheduled_hourly'
}
app_handler(event, dummy_context)
