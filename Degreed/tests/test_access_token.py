import unittest
from parameterized import parameterized
import requests_mock
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
degreed_base_url = app_settings.get("degreed_base_url")
# token_url
token_url = "https://" + degreed_base_url
# given valid token
valid_token = token_string.get_token_string()


class AccessTokenTest(unittest.TestCase):
    """
    Given valid candidate id
    test that a token returing by get_access_token function is correctly
    """

    def test_get_access_token_valid_client_id(self):
        # Mock 'requests' module 'post' method.
        mock_post_patcher = patch("lambda_function.requests.post")
        # Start patching 'requests.post'.
        mock_post = mock_post_patcher.start()
        # Configure the mock to return a response with status code 200.
        mock_post.return_value.status_code = 200
        # Configure the mock to return a response with access token.
        mock_post.return_value.json.return_value = {
            "access_token": valid_token,
            "token_type": "bearer",
            "expires_in": 5183999,
            "refresh_token": "4cfc971e671a4cc5afbda32527f6e9c472bdfc6c77c64ee7a6fdc8a2f6e5a54b",
        }
        # Call the function, which will send a request to the server.
        token = lambda_function.get_access_token(app_settings, token_url)
        # Stop patching 'requests'.
        mock_post_patcher.stop()
        # Assert that the request-response cycle completed successfully.
        self.assertEqual(valid_token, token)

    """
    Given invalid and blank credentials
    test that a response status code 500 by calling get_access_token function
    """

    @parameterized.expand(
        [
            ["degreed_client_id", "7b5a18386173507", {"statusCode": 500, "body": 
                '{"error": "Request failed. Status code: 500. Reason: None."}'}],
            ["degreed_client_id", "", {"statusCode": 500, "body": 
                '{"error": "Request failed. Status code: 500. Reason: None."}'}],
            ["degreed_client_secret", "259ad32f98f366ea5b29b9cb", {"statusCode": 500, "body": 
                '{"error": "Request failed. Status code: 500. Reason: None."}'}],
            ["degreed_client_secret", "", {"statusCode": 500, "body": 
                '{"error": "Request failed. Status code: 500. Reason: None."}'}],
        ]
    )
    def test_get_access_token_crendentials(self, arg1, arg2, expected):
        # make client id invalid
        app_settings.update({arg1: arg2})

        with requests_mock.Mocker() as mock:
            mock.post(token_url + "/oauth/token", status_code=500)
            response = lambda_function.get_access_token(app_settings, token_url)
            self.assertEqual(expected.get("statusCode"), response.get("statusCode"))
            self.assertEqual(expected.get("body"), response.get("body", {}))
