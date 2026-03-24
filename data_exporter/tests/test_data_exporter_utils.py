import unittest
from unittest import mock
import data_exporter_utils
from data_exporter_utils import IncorrectOutputFileFormatException, DeliveryTimeException
from db.table_registry import UnknownTableException
class TestRetryDecorator(unittest.TestCase):

    @mock.patch('requests.post')
    def test_retry_on_failure(self, mock_post):
        mock_response = mock.Mock()
        mock_response.status_code = 500  # Non-200 status code to trigger retry
        mock_post.return_value = mock_response

        response = data_exporter_utils.post_request_with_retries('http://testurl.com', {}, {}, 5)

        # Assert that the request was retried the correct number of times
        self.assertEqual(mock_post.call_count, 3)  # Default number of retries is 3
        # Assert that the response was returned even if it was a failure
        self.assertEqual(response.status_code, 500)

    @mock.patch('requests.post')
    def test_success_after_retry(self, mock_post):
        mock_response_fail = mock.Mock()
        mock_response_fail.status_code = 500
        mock_response_success = mock.Mock()
        mock_response_success.status_code = 200

        # First time, request fails. Second time, it succeeds.
        mock_post.side_effect = [mock_response_fail, mock_response_success]

        response = data_exporter_utils.post_request_with_retries('http://testurl.com', {}, {}, 5)

        # Assert that the request was retried the correct number of times
        self.assertEqual(mock_post.call_count, 2)
        # Assert that the successful response was returned
        self.assertEqual(response.status_code, 200)


class TestUtilFunction(unittest.TestCase):

    def test_validate_json(self):
        app_setting = {
            "output_file_formats": {
                "positions": {
                    "data_filename_format": "{output_date_format}_efld_0_position.json",
                    "meta_filename_format": "{output_date_format}_efld_0_position.meta"
                }
            },
            "output_date_format": ""
        }
        # Missing output_date_format
        with self.assertRaises(IncorrectOutputFileFormatException) as ex:
            data_exporter_utils.validate_json(app_setting)
            self.assertEqual(str(ex), 'output_date_format is required when output_file_formats contains {output_date_format}')

        app_setting = {
            "output_file_formats": {
                "positions": {
                    "data_filename_format": "{output_date_format}_efld_0_position",
                    "meta_filename_format": "{output_date_format}_efld_0_position"
                }
            },
            "output_date_format": ""
        }
        # Duplicate filename
        with self.assertRaises(IncorrectOutputFileFormatException) as ex:
            data_exporter_utils.validate_json(app_setting)
            self.assertEqual(str(ex), 'data_filename_format and meta_filename_format cannot be the same')

        app_setting = {
            "output_file_formats": {
                "random": {
                    "data_filename_format": "{output_date_format}_efld_0_position.json",
                    "meta_filename_format": "{output_date_format}_efld_0_position.meta"
                }
            },
            "output_date_format": "%Y%m%d_%H%M%S"
        }
        # Duplicate filename
        with self.assertRaises(UnknownTableException) as ex:
            data_exporter_utils.validate_json(app_setting)

        app_setting = {
            "output_file_formats": {
                "positions": {
                    "data_filename_format": "{output_date_format}_efld_0_position.json",
                    "meta_filename_format": "{output_date_format}_efld_0_position.meta"
                }
            },
            "output_date_format": "%Y%m%d_%H%M%S"
        }
        data_exporter_utils.validate_json(app_setting)

    def test_validate_delivery_time(self):
        app_setting = { "delivery_time": "12:00" }
        data_exporter_utils.validate_delivery_time(app_setting)

        app_setting = { "delivery_time": "12:00:00" }
        data_exporter_utils.validate_delivery_time(app_setting)

        app_setting = { "delivery_time": "12" }
        data_exporter_utils.validate_delivery_time(app_setting)

        app_setting = { "delivery_time": "25:00" }
        with self.assertRaises(DeliveryTimeException):
            data_exporter_utils.validate_delivery_time(app_setting)

        app_setting = { "delivery_time": "12.00" }
        with self.assertRaises(DeliveryTimeException):
            data_exporter_utils.validate_delivery_time(app_setting)

        app_setting = { "delivery_time": "13:00:00.0000" }
        with self.assertRaises(DeliveryTimeException):
            data_exporter_utils.validate_delivery_time(app_setting)
