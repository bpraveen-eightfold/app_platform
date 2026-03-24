import json

import requests

from html_builder import HtmlBuilder

BASE_URL = 'https://api-test-products.heidrick.com'
AUTH_ENDPOINT = '/auth/api/v2/auth'
ATTACHMENT_ENDPOINT = '/profile/api/v2/attachments'

class HsApiClient:
    def __init__(self, client_id, client_secret, username, base_url=None):
        """
        Intialize API client with authentication header

        Args:
            client_id: API credential client ID
            client_secret: API credential client secret
            username: API credential username associated with ID and secret
        """
        self.base_url = base_url or BASE_URL
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.access_token = None
        self.headers = None

        self.access_token = self.get_access_token()
        self.headers = self.get_headers()
    
    def get_access_token(self):
        """
        Requests API access token using client ID and secret
        """
        if not self.access_token:
            url = self.base_url + AUTH_ENDPOINT
            payload = {
                'authClientId': self.client_id,
                'authClientSecret': self.client_secret,
                'username': self.username,
            }

            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            resp_body = resp.json()
            self.access_token = resp_body.get('data', {}).get('accessToken') or ''
        return self.access_token

    def get_headers(self):
        """
        Constructs the request header with Authorization using access token
        """
        if self.headers is None:
            self.headers = {}
        if 'Authorization' not in self.headers:
            self.headers['Authorization'] = f'Bearer {self.get_access_token()}'
        return self.headers

    def get_assessment_attachments(self):
        """
        For the given profile, request assessment data through
        H&S API endpoint, and return the data.
        """
        url = self.base_url + ATTACHMENT_ENDPOINT
        params = {}
        resp = requests.get(url, headers=self.headers, params=params)
        if 400 <= resp.status_code < 500:
            resp.raise_for_status()
        resp_json = resp.json()
        return resp_json.get('data') or []


def safe_get_int(s, default=3):
    """
    convert string to int
    """
    if not s:
        return default
    try:
        ret = int(s)
    except ValueError:
        return default
    return ret


def assessment_reports_handler(event, context):
    """
    Construct HTML text of the app widget.
    The data is fetched through API request to H&S.

    Returns HTML of the widget
    """
    request_data = event.get('request_data', {})
    app_settings = event.get('app_settings', {})

    email = request_data.get('email')
    emails = request_data.get('all_emails', [])
    username = email or (emails[0] if emails else None)

    client_id = app_settings.get('client_id', '')
    client_secret = app_settings.get('client_secret', '')
    max_shown = safe_get_int(app_settings.get('max_shown'))     # Max number of assessments shown in the widget
    base_url = app_settings.get('base_url')

    if not username:
        raise ValueError('No email found for the given profile in request data')

    client = HsApiClient(client_id, client_secret, username, base_url)
    resp_data = client.get_assessment_attachments()
    resp_data = resp_data[:max_shown]

    builder = HtmlBuilder(resp_data, username)
    return builder.construct_widget_html()


def app_handler(event, context):
    """
    Entry point for app code
    """
    html = ''
    try:
        if event.get('trigger_name') == 'career_hub_profile_view':
            html = assessment_reports_handler(event, context)
    except requests.HTTPError as http_error:
        print(http_error)
        if http_error.response.status_code == 404:
            html = HtmlBuilder.construct_empty_widget_html()
        else:
            return {
                'statusCode': http_error.response.status_code,
                'body': json.dumps({'error': str(http_error)}),
            }
        
    except Exception as ex:
        print(str(ex))
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ex) or 'Internal Error'}),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({"html": html, 'data': {}, 'cache_ttl_seconds': 1800})
    }


if __name__ == '__main__':
    """
    Fill in the details in the event dict and invoke this 
    script for e2e testing/debugging with breakpoints.
    """
    event = {
        'trigger_name': 'career_hub_profile_view',
        'app_settings': {
            'client_id': '',
            'client_secret': '',
        },
        'request_data': {
            'all_emails': [],
            'email': ''
        }
    }
    resp = app_handler(event, {})
