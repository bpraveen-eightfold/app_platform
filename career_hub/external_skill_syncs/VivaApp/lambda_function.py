import json
import requests
import traceback
from requests.exceptions import Timeout
from ef_app_sdk import EFAppSDK

CRT_PATH = 'eightfold_viva_skills_auth.crt'
KEY_PATH = 'eightfold_viva_skills_auth.key'

def error_response(error_str):
    """Error Response message"""
    error = {'error': error_str}
    print(json.dumps(error))
    return {
        'statusCode': 500,
        'body': json.dumps(error)
    }

class VivaClient:
    def __init__(self, app_settings, request_data, app_sdk):
        self.app_settings = app_settings
        self.request_data = request_data
        self.base_url_oauth = app_settings.get("base_url_oauth", '')
        self.base_url_certs = app_settings.get("base_url_certs", '')
        self.headers = self.get_headers()
        self.employee_id = self.get_employee_id()
        self.cert_path = self.get_cert_path()
        self.endpoint_oauth = f"/{app_settings.get('endpoint_oauth', '')}"
        self.endpoint_certs = f"/{app_settings.get('endpoint_certs', '')}"
        self.request_timeout = app_settings.get('request_timeout') or 4
        self.app_sdk = app_sdk

    def get_headers(self, oauth_token=None, content_type=None):
        headers = {
            'Ocp-Apim-Subscription-Key': self.app_settings.get('subscription_key', '')
        }
        
        if oauth_token:
            headers['Authorization'] = f'Bearer {oauth_token}'
        
        if content_type:
            headers['Content-Type'] = content_type
        
        return headers

    def get_employee_id(self):
        return self.app_settings.get("test_employee_id") or self.request_data.get("employee_id")

    def get_cert_path(self):
        return (self.app_settings.get('crt_path') or CRT_PATH, self.app_settings.get('key_path') or KEY_PATH)

    def handle_sync_skills_trigger(self, request_data):
        response = requests.Response()
        is_external_skills_oauth_gate_enabled = self.app_settings.get('external_skills_oauth_gate_enabled', False)

        if is_external_skills_oauth_gate_enabled:
            oauth_token = request_data.get('oauth_token')
            
            if not oauth_token:
                raise Exception('OAuth token is missing.')
            
            headers = self.get_headers(oauth_token)
            try:
                response = requests.get(
                    self.base_url_oauth + self.endpoint_oauth, headers=headers, timeout=self.request_timeout
                )
            except Timeout:
                raise Exception('Request timed out for GET skills API.')
        else:
            if not self.employee_id:
                raise Exception("Employee id is missing.")

            self.app_sdk.log(f'Invoking Viva GET API for {self.employee_id}')

            try:
                endpoint = f"{self.endpoint_certs}/{self.employee_id}"
                response = requests.get(
                    self.base_url_certs + endpoint, headers=self.headers, cert=self.cert_path, timeout=self.request_timeout
                )
            except Timeout:
                raise Exception('Request timed out for GET skills API.')

        if response.status_code != 200:
            raise Exception(f'Failed to get skills. Status code: {response.status_code}. Reason: {response.reason}.')
        
        return response.json() if is_external_skills_oauth_gate_enabled else response.json().get('data', [])

    def handle_writeback_skills_trigger(self, request_data):
        is_external_skills_oauth_gate_enabled = self.app_settings.get('external_skills_oauth_gate_enabled', False)

        if self.app_settings.get('test_writeback_code'):
            return self.app_settings.get('test_writeback_code')

        payload = json.dumps(
            {
                'data': request_data.get('skills_data')
            }
        )

        if is_external_skills_oauth_gate_enabled:
            oauth_token = request_data.get('oauth_token')
            
            if not oauth_token:
                raise Exception('OAuth token is missing.')
                
            headers = self.get_headers(oauth_token=oauth_token, content_type='application/json')

            response = requests.put(
                self.base_url_oauth + self.endpoint_oauth, headers=headers, data=payload
            )
        else:
            if not self.employee_id:
                raise Exception("Employee id is missing.")

            endpoint = f"{self.endpoint_certs}/{self.employee_id}"
            response = requests.put(
                self.base_url_certs + endpoint, headers=self.headers, data=payload, cert=self.cert_path
            )

        if response.status_code != 200:
            raise Exception(f'Failed to write skills. Status code: {response.status_code}. Reason: {response.reason}.')
        
        return 200

def app_handler(event, context):
    app_sdk = EFAppSDK(context)
    app_sdk.log('Starting App Invocation')
    request_data = event.get('request_data', {})
    trigger_name = event.get('trigger_name')
    app_settings = event.get('app_settings', {})
    viva_client = VivaClient(app_settings, request_data, app_sdk)
    app_sdk.log(f"Is External Skills Oauth Gate Enabled: {app_settings.get('external_skills_oauth_gate_enabled', False)}")

    data = None
    try:
        if trigger_name == 'sync_external_skills':
            app_sdk.log('Handling sync skills trigger')
            data = viva_client.handle_sync_skills_trigger(request_data)
        elif trigger_name == 'writeback_external_skills':
            app_sdk.log('Handling writeback skills trigger')
            app_sdk.log(f'Writeback Skills Data: {request_data.get("skills_data")}')
            data = viva_client.handle_writeback_skills_trigger(request_data)

        if data is None:
            return error_response('Unknown trigger.')
        
        app_sdk.log(f'Data: {data}')
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data }),
        }

    except Exception as ex:
        print('Something went wrong, traceback: {}'.format(traceback.format_exc()))
        app_sdk.log(f'Error: {repr(ex)}')
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
