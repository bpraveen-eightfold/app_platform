import unittest
import mock
import requests
import json
import six

from lambda_function import app_handler

def make_http_response(status_code, content):
    http_response = mock.MagicMock()
    http_response.status_code = status_code
    if isinstance(content, list):
        content = json.dumps(content).encode('utf-8')
    http_response.content = maybe_str_to_bytes(content)
    return http_response


def maybe_str_to_bytes(input_str):
    if not six.PY2 and not isinstance(input_str, bytes):
        return bytes(input_str, 'utf-8')
    return input_str


def mocked_requests(**kwargs):
    if kwargs['url'] == 'https://oauth.com/':
        return make_http_response(200, '{"grant_type":"Bearer", "access_token":"token"}')
    elif 'https://mera.com/' in kwargs['url']:
        mock_resp = [
            {
                "GPN": "CA010007600",
                "GUI": "2004521",
                "ExternalConfirmedAvlPct": 100.000000,
                "ExternalAvlPct": 100.000000,
                "TotalConfirmedAvlPct": 100.000000
            },
            {
                "GPN": "CA013245609",
                "GUI": "2015535",
                "ExternalConfirmedAvlPct": 100.000000,
                "ExternalAvlPct": 100.000000,
                "TotalConfirmedAvlPct": 100.000000
            }
        ]
        return make_http_response(200, mock_resp)
    elif 'https://mera2.com' in kwargs['url']:
        mock_resp = [
            {
                "GPN_ID": "CA010007600",
                "ExternalAvlPct": 100.000000,
                "TotalConfirmedAvlPct": 100.000000
            }
        ]
        return make_http_response(200, mock_resp)
    return make_http_response(400, None)


class TestLambdaFunction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.response_body_success = {
            "data": {
                "actions": [
                    {
                        "action_name": "store_employee_availability_data",
                        "request_data": {
                            "employees_availability": [
                                {
                                    "employee_id": "CA010007600",
                                    "external_avl_pct": 100.0,
                                    "external_confirmed_avl_pct": 100.0,
                                    "total_confirmed_avl_pct": 100.0
                                },
                                {
                                    "employee_id": "CA013245609",
                                    "external_avl_pct": 100.0,
                                    "external_confirmed_avl_pct": 100.0,
                                    "total_confirmed_avl_pct": 100.0
                                }
                            ]
                        }
                    }
                ]
            }
        }


    @mock.patch('requests.get', side_effect=mocked_requests)
    @mock.patch('requests.post', side_effect=mocked_requests)
    def test_app_handler(self, mock_request_get, mock_request_post):
        mock_app_settings = {
                'oauth_settings': {
                'url': 'https://oauth.com/',
                'grant_type': 'client_credentials',
                'client_id': 'client_id',
                'client_secret': 'client_secret',
                'resource': 'resource'
            },
            'api_url': 'https://mera.com'
        }

        event = {
            'trigger_name': 'employee_availability_fetch',
            'app_settings': mock_app_settings,
        }

        # Case 1: Success
        request_data = {
            'employee_ids': [
                "CA010007600",
                "CA013245609"
            ],
            'start_date': "2022-07-01",
            'end_date': "2022-07-15"
        }
        event['request_data'] = request_data
        resp = app_handler(event=event, context=None)
        self.assertEqual(resp['statusCode'], 200)
        self.assertDictEqual(json.loads(resp['body']), self.response_body_success)

        # Case 2: Status code NOT 200 in API Response
        mock_app_settings['api_url'] = 'https://ey-mera.com/'
        event['app_settings'] = mock_app_settings
        resp = app_handler(event=event, context=None)
        self.assertEqual(resp['statusCode'], 500)


        # Case 3: Response not formatted as expected
        mock_app_settings['api_url'] = 'https://mera2.com/'
        event['app_settings'] = mock_app_settings
        resp = app_handler(event=event, context=None)
        self.assertEqual(resp['statusCode'], 500)

        # Case 4: Request data not formatted correctly
        mock_app_settings['api_url'] = 'https://mera.com/'
        event['app_settings'] = mock_app_settings
        request_data = {
            'ids': [
                "CA010007600",
                "CA013245609"
            ],
            'startdate': "2022-07-01",
            'end_date': "2022-07-15"
        }
        event['request_data'] = request_data
        resp = app_handler(event=event, context=None)
        self.assertEqual(resp['statusCode'], 400)
