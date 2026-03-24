import mock
import unittest

import requests

import lambda_function
from lambda_function import HsApiClient


client_id = 'test-client-id'
client_secret = 'test-client-secret'
username = 'test-username'
base_url = 'test-base-url'

class TestHsApiClient(unittest.TestCase):
    @mock.patch('lambda_function.HsApiClient.get_headers')
    @mock.patch('lambda_function.HsApiClient.get_access_token')
    def test_constructor(self, mock_get_access_token, mock_get_headers):
        client = HsApiClient(client_id, client_secret, username, base_url)

        self.assertEqual(client.client_id, 'test-client-id')
        self.assertEqual(client.client_secret, 'test-client-secret')
        self.assertEqual(client.username, 'test-username')
        self.assertEqual(client.base_url, 'test-base-url')
        
        mock_get_access_token.assert_called()
        mock_get_headers.assert_called()

    @mock.patch('requests.post')
    def test_get_access_token(self, mock_post):
        mock_post.return_value = mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'data': {
                'accessToken': 'test-access-token'
            }
        }
        
        client = HsApiClient(client_id, client_secret, username, base_url)
        self.assertEqual(client.access_token, 'test-access-token')
        mock_post.assert_called_once_with('test-base-url/api/v1/auth', json={
            'authClientId': 'test-client-id',
            'authClientSecret': 'test-client-secret',
            'username': 'test-username',
        })

        mock_post.reset_mock()
        client.get_access_token()
        self.assertEqual(client.access_token, 'test-access-token')
        mock_post.assert_not_called()

    @mock.patch('lambda_function.HsApiClient.get_access_token')
    def test_get_headers(self, mock_get_access_token):
        mock_get_access_token.return_value = 'test-access-token'
        client = HsApiClient(client_id, client_secret, username, base_url)
        self.assertEqual(client.headers, {'Authorization': 'Bearer test-access-token'})

    @mock.patch('requests.get')
    @mock.patch('lambda_function.HsApiClient.get_access_token')
    def test_get_assessment_attachments(self, mock_get_access_token, mock_get):
        mock_get_access_token.return_value = 'test-access-token'
        mock_get.return_value = mock_resp = mock.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'data': [{'key': 'value'}]}
        client = HsApiClient(client_id, client_secret, username, base_url)

        attachments = client.get_assessment_attachments()
        mock_get.assert_called_with(
            'test-base-url/api/v1/attachments',
            headers={'Authorization': 'Bearer test-access-token'},
            params={'category': 'Assessment'}
        )
        self.assertEqual(attachments, [{'key': 'value'}])

class TestLambdaFunction(unittest.TestCase):
    def setUp(self):
        self.event = {
            'trigger_name': 'career_hub_profile_view',
            'app_settings': {
                'client_id': 'test-client-id',
                'client_secret': 'test-client-secret',
                'max_shown': 1,
                'base_url': 'test-base-url'
            },
            'request_data': {
                'all_emails': [],
                'email': 'testuser@example.com'
            }
        }

    @mock.patch('html_builder.HtmlBuilder.construct_widget_html')
    @mock.patch('lambda_function.HsApiClient.get_assessment_attachments')
    @mock.patch('lambda_function.HsApiClient.get_access_token')
    def test_app_handler(self, 
                         mock_get_access_token, 
                         mock_get_assessment_attachments,
                         mock_construct_widget_html):
        mock_get_access_token.return_value = 'test-access-token'
        mock_get_assessment_attachments.return_value = [
            {'reportName': 'report 1'},
            {'reportName': 'report 2'},
            {'reportName': 'report 3'}
        ]
        mock_construct_widget_html.return_value = '<div></div>'
        
        resp = lambda_function.app_handler(self.event, context={})
        mock_get_assessment_attachments.assert_called()
        mock_construct_widget_html.assert_called_with()
        self.assertEqual(resp, {
            'statusCode': 200,
            'body': '{"html": "<div></div>", "data": {}, "cache_ttl_seconds": 1800}'
        })

    @mock.patch('requests.get')
    @mock.patch('lambda_function.HsApiClient.get_access_token')
    def test_app_handler_404(self, 
                         mock_get_access_token, 
                         mock_get):
        mock_get_access_token.return_value = 'test-access-token'

        mock_error = mock.MagicMock()
        mock_error.status_code = 404
        mock_get.return_value = mock_error

        http_error = requests.HTTPError(404, '')
        http_error.response = mock_error
        mock_error.raise_for_status.side_effect = http_error
        
        resp = lambda_function.app_handler(self.event, context={})
        self.assertEqual(resp.get('statusCode'), 200)

if __name__ == '__main__':
    unittest.main()
