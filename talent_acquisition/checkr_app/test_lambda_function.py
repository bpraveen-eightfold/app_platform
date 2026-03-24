import unittest
from unittest.mock import patch, Mock
import json
from datetime import datetime, timezone

# Import the functions from your script
from lambda_function import (
    error_response, success_response, convert_to_timestamp, str2bool, 
    list_tests, invite_candidate, validate_work_location,
    get_candidate, create_new_candidate, invite_existing_candidate,
    is_webhook_supported, handle_webhook_event, app_handler
)

class TestFunctions(unittest.TestCase):

    def test_error_response(self):
        error_str = 'This is an error'
        response = error_response(500, error_str)
        expected_response = {
            'statusCode': 500,
            'body': json.dumps({'data': {'error': error_str, 'error_code': 500}})
        }
        self.assertEqual(response, expected_response)

    def test_success_response(self):
        data = {'key': 'value'}
        response = success_response(data)
        expected_response = {
            'statusCode': 200,
            'body': json.dumps({'data': data})
        }
        self.assertEqual(response, expected_response)

    def test_convert_to_timestamp(self):
        time_str = '2023-07-19T12:34:56Z'
        expected_timestamp = int(datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp())
        self.assertEqual(convert_to_timestamp(time_str), expected_timestamp)

    def test_str2bool(self):
        self.assertTrue(str2bool('yes'))
        self.assertTrue(str2bool('true'))
        self.assertFalse(str2bool('no'))
        self.assertFalse(str2bool('false'))

    @patch('requests.get')
    def test_list_tests(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'slug1', 'slug': 'test_slug_1', 'name': 'Test 1'},
                {'id': 'slug2', 'slug': 'test_slug_2', 'name': 'Test 2'}
            ]
        }
        mock_get.return_value = mock_response

        request_data = {'oauth_token': 'token'}
        app_settings = {'checkr_base_url': 'https://api.checkr.com'}
        response = list_tests(request_data, app_settings)
        expected_data = [
            {'duration_minutes': '', 'id': 'test_slug_1', 'name': 'Test 1 - Test 1', 'published': ''},
            {'duration_minutes': '', 'id': 'test_slug_2', 'name': 'Test 1 - Test 2', 'published': ''},
            {'duration_minutes': '', 'id': 'test_slug_1', 'name': 'Test 2 - Test 1', 'published': ''},
            {'duration_minutes': '', 'id': 'test_slug_2', 'name': 'Test 2 - Test 2', 'published': ''}
        ]
        expected_response = success_response(expected_data)
        self.assertEqual(response, expected_response)

    @patch('requests.get')
    @patch('requests.post')
    def test_invite_candidate(self, mock_post, mock_get):
        mock_get_candidate_response = Mock()
        mock_get_candidate_response.status_code = 200
        mock_get_candidate_response.json.return_value = {'data': []}
        mock_get.return_value = mock_get_candidate_response

        mock_create_candidate_response = Mock()
        mock_create_candidate_response.status_code = 200
        mock_create_candidate_response.json.return_value = {'id': 'candidate_id', 'email': 'test@example.com'}
        mock_post.return_value = mock_create_candidate_response

        mock_invite_response = Mock()
        mock_invite_response.status_code = 200
        mock_invite_response.json.return_value = {'id': 'invite_id', 'invitation_url': 'test_url', 'email': 'test@example.com', 'candidate_id': 'candidate_id'}
        mock_post.return_value = mock_invite_response

        request_data = {
            'oauth_token': 'token',
            'first_name': 'John',
            'last_name': 'Doe',
            'location_state': 'CA,US',
            'invite_metadata': {
                'email': 'test@example.com',
                'pid': '123',
                'profile_id': 'profile_123',
                'ats_candidate_id': 'ats_123',
                'test_id': 'test_123'
            }
        }
        app_settings = {'checkr_base_url': 'https://api.checkr.com', 'use_test_email': 'False'}
        response = invite_candidate(request_data, app_settings)
        expected_data = {
            'assessment_id': 'invite_id',
            'invite_already_sent': '',
            'email': 'test@example.com',
            'test_url': 'test_url',
            'vendor_candidate_id': 'candidate_id'
        }
        expected_response = success_response(expected_data)
        self.assertEqual(response, expected_response)

    def test_validate_work_location(self):
        self.assertEqual(validate_work_location('CA,US'), 'CA')
        self.assertEqual(validate_work_location('US'), 'CA')
        self.assertIsNone(validate_work_location(''))

    @patch('requests.get')
    def test_get_candidate(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': [{'id': 'candidate_id'}]}
        mock_get.return_value = mock_response

        candidate = get_candidate('https://api.checkr.com', 'token', 'John', 'Doe', 'test@example.com')
        self.assertEqual(candidate['id'], 'candidate_id')

    @patch('requests.post')
    def test_create_new_candidate(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'candidate_id'}
        mock_post.return_value = mock_response

        candidate_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'test@example.com',
            'metadata[pid]': '123',
            'metadata[profile_id]': 'profile_123',
            'metadata[ats_candidate_id]': 'ats_123',
            'metadata[test_id]': 'test_123',
            'metadata[email]': 'test@example.com'
        }
        candidate = create_new_candidate('https://api.checkr.com', 'token', 'John', 'Doe', 'test@example.com', candidate_data)
        self.assertEqual(candidate['id'], 'candidate_id')

    @patch('requests.post')
    def test_invite_existing_candidate(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'invite_id', 'invitation_url': 'test_url', 'candidate_id': 'candidate_id'}
        mock_post.return_value = mock_response

        candidate = {'id': 'candidate_id'}
        invite_metadata = {'test_id': 'test_123'}
        invite = invite_existing_candidate('https://api.checkr.com', 'token', candidate, invite_metadata, 'CA')
        self.assertEqual(invite['id'], 'invite_id')

    def test_is_webhook_supported(self):
        response = is_webhook_supported()
        expected_response = success_response({'is_webhook_supported': 'true'})
        self.assertEqual(response, expected_response)

    @patch('requests.get')
    def test_handle_webhook_event(self, mock_get):
        mock_candidate_response = Mock()
        mock_candidate_response.status_code = 200
        mock_candidate_response.json.return_value = {
            'metadata': {
                'email': 'test@example.com',
                'profile_id': 'profile_123',
                'pid': '123',
                'ats_candidate_id': 'ats_123',
                'test_id': 'test_123'
            }
        }
        mock_get.return_value = mock_candidate_response

        request_data = {
            'oauth_token': 'token',
            'request_payload': {
                'type': 'report.completed',
                'data': {
                    'object': {
                        'id': 'report_id',
                        'candidate_id': 'candidate_id',
                        'status': 'complete',
                        'completed_at': '2023-07-19T12:34:56Z',
                        'created_at': '2023-07-19T10:00:00Z',
                        'result': 'clear'
                    }
                }
            }
        }
        app_settings = {'checkr_report_base_url': 'https://api.checkr.com'}
        response = handle_webhook_event(request_data, app_settings)
        expected_data = {
            'stacktrace': '',
            'actions': [{
                'action_name': 'save_assessment_to_profile_data',
                'request_data': {
                    'invite_metadata': {
                        'email': 'test@example.com',
                        'profile_id': 'profile_123',
                        'pid': '123',
                        'ats_candidate_id': 'ats_123',
                        'test_id': 'test_123'
                    },
                    'assessment_report': {
                        'test_id': 'test_123',
                        'email': 'test@example.com',
                        'status': 'completed',
                        'vendor_report_status': 'complete',
                        'rating': None,
                        'assigned_ts': 1689760800,
                        'start_ts': 1689760800,
                        'completed_ts': 1689770096,
                        'comments': 'No comments available.',
                        'report_url': 'https://api.checkr.com/report_id',
                        'response_json': request_data['request_payload'],
                        'vendor_status': 'Unknown'
                    }
                }
            }],
            'is_success': True,
            'error': False
        }
        expected_response = success_response(expected_data)
        self.assertEqual(response, expected_response)

    @patch('lambda_function.get_logo_url')
    @patch('lambda_function.list_tests')
    @patch('lambda_function.invite_candidate')
    @patch('lambda_function.is_webhook_supported')
    @patch('lambda_function.handle_webhook_event')
    def test_app_handler(self, mock_handle_webhook_event, mock_is_webhook_supported, mock_invite_candidate, mock_list_tests, mock_get_logo_url):
        event = {
            'request_data': {'key': 'value'},
            'app_settings': {'key': 'value'},
            'trigger_name': 'assessment_get_logo_url'
        }
        mock_get_logo_url.return_value = success_response({'logo_url': 'https://assets.checkr.com/logo-blue.svg'})
        response = app_handler(event, {})
        self.assertEqual(response, success_response({'logo_url': 'https://assets.checkr.com/logo-blue.svg'}))
        
        event['trigger_name'] = 'assessment_list_tests'
        mock_list_tests.return_value = success_response([{'id': 'test_1', 'name': 'Test 1'}])
        response = app_handler(event, {})
        self.assertEqual(response, success_response([{'id': 'test_1', 'name': 'Test 1'}]))

        event['trigger_name'] = 'assessment_invite_candidate'
        mock_invite_candidate.return_value = success_response({'assessment_id': 'test_id'})
        response = app_handler(event, {})
        self.assertEqual(response, success_response({'assessment_id': 'test_id'}))

        event['trigger_name'] = 'assessment_is_webhook_supported'
        mock_is_webhook_supported.return_value = success_response({'is_webhook_supported': 'true'})
        response = app_handler(event, {})
        self.assertEqual(response, success_response({'is_webhook_supported': 'true'}))

        event['trigger_name'] = 'webhook_receive_event'
        mock_handle_webhook_event.return_value = success_response({'key': 'value'})
        response = app_handler(event, {})
        self.assertEqual(response, success_response({'key': 'value'}))

if __name__ == '__main__':
    unittest.main()