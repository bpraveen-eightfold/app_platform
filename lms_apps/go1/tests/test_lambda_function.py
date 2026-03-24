import mock
import requests
import unittest

import lambda_function


class TestLambdaFunction(unittest.TestCase):
    @mock.patch('requests.post')
    def test_get_access_token(self, mock_post):
        mock_client_id = 'client_id'
        mock_client_secret = 'client_secret'
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {'token_type': 'bearer', 'access_token': 'access_token'}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        token_type, access_token = lambda_function.get_access_token(mock_client_id, mock_client_secret)

        mock_post.assert_called_once_with(
            url='https://auth.go1.com/oauth/token',
            data={
                'client_id': 'client_id',
                'client_secret': 'client_secret',
                'grant_type': 'client_credentials',
            }
        )
        self.assertEqual(token_type, 'bearer')
        self.assertEqual(access_token, 'access_token')

        # Check if function raises requests.HTTPError when response returns an error
        mock_error_response = requests.Response()
        mock_error_response.status_code = 400
        mock_post.return_value = mock_error_response
        with self.assertRaises(requests.HTTPError):
            token_type, access_token = lambda_function.get_access_token(mock_client_id, mock_client_secret)

    def test_convert_field_names(self):
        learning_object = {
            'id': '1234',
            'title': 'example title',
            'description': 'example description',
            'summary': 'example summary',
            'language': 'example language',
            'image': 'example image url',
            'type': 'example type',
            'delivery': {'duration': 1},
            'provider': {'name': 'example provider'},
            'created_time': 1234,
            'assessable': True,
        }
        expected_learning_object = {
            'id': '1234',
            'title': 'example title',
            'description': 'example description',
            'summary': 'example summary',
            'language': 'example language',
            'image_url': 'example image url',
            'content_type': 'example type',
            'duration': 1,
            'portal': 'example provider',
            'created': 1234,
            'assessable': True,
            'enrolments': None,
            'sourceId': None,
            'mobile_optimised': None,
            'wcag': None,
            'internal_qa_rating': None,
        }
        new_learning_object = lambda_function.convert_field_names(learning_object)
        self.assertEqual(new_learning_object, expected_learning_object)

    @mock.patch('time.time')
    def test_get_csv_filename(self, mock_timestamp):
        filename_prefix = 'test'
        timestamp_format = '%Y%m%d_%H%M%S'
        mock_timestamp.return_value = 1665448755

        filename = lambda_function.get_csv_filename(filename_prefix, timestamp_format)
        self.assertEqual(filename, '/tmp/test_20221011_003915.csv')
