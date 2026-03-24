import unittest
from parameterized import parameterized
from unittest.mock import patch
from fake_data import inputs, token_string
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# degree baseurl
edcast_base_url = app_settings.get("edcast_base_url")
# email
email = app_settings.get("edcast_test_email")
# token_url
token_url = "https://" + edcast_base_url
# given valid token
valid_token = token_string.get_token_string()


class AccessTokenTest(unittest.TestCase):
    """
    Given valid candidate id
    test that a token returning by get_access_token function is correctly
    """

    @parameterized.expand(
        [
            ["edcast_api_key", "7b5a18386173507b", 200, valid_token],
            ["edcast_api_key", "7b5a18386173507", 500, 500],
            ["edcast_api_key", "", 500, 500],
            ["edcast_client_secret", "259ad32f98f366ea5b29b9cb", 500, 500],
            ["edcast_client_secret", "", 500, 500],
        ]
    )
    def test_get_access_token_valid_client_id(self, arg1, arg2, status_code, expected):
        # make client id invalid
        app_settings.update({arg1: arg2})
        # Mock 'requests' module 'post' method.
        mock_post_patcher = patch("lambda_function.requests.get")
        # Start patching 'requests.post'.
        mock_post = mock_post_patcher.start()
        # Configure the mock to return a response with status code 200.
        mock_post.return_value.status_code = status_code
        if status_code == 200:
            # Configure the mock to return a response with access token.
            mock_post.return_value.json.return_value = {"jwt_token": valid_token}
        # Call the function, which will send a request to the server.
        response = lambda_function.get_access_token(app_settings, token_url, email)
        # Stop patching 'requests'.
        mock_post_patcher.stop()
        if status_code == 200:
            # Assert that the request-response cycle completed successfully.
            self.assertEqual(expected, response)
        else:
            self.assertEqual(expected, response.get("statusCode"))
