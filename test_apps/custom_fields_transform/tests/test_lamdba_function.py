import pytest
import uuid
from unittest import TestCase
from unittest.mock import patch
import lambda_function


class TestResponseS3Key(TestCase):
    def setUp(self):
        self.request_info = {
            'event_type': 'fetch',
            'transform_op': 'custom_op',
            'group_id': 'group123',
            'system_id': 'sys456'
        }

    @patch('uuid.uuid4', return_value=uuid.UUID('deadc0dedeadc0dedeadc0dedeadc0de'))
    def test_get_response_s3_key_mocked_uuid(self, mock_uuid4):
        expected = f"{lambda_function.BASE_S3_DIRECTORY}/group123/sys456/fetch/custom_op_resp/deadc0dedeadc0dedeadc0dedeadc0de"
        result = lambda_function._get_response_s3_key(self.request_info)
        self.assertEqual(result, expected)

    def test_get_response_s3_key_unmocked_uuid(self):
        expected_prefix = f"{lambda_function.BASE_S3_DIRECTORY}/group123/sys456/fetch/custom_op_resp"
        result = lambda_function._get_response_s3_key(self.request_info)
        self.assertTrue(result.startswith(expected_prefix))
