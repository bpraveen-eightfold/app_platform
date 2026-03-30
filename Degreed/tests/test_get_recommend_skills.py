import unittest
from parameterized import parameterized
from unittest.mock import patch
from fake_data import fake_course, inputs, token_string
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# degree baseurl
degreed_base_url = app_settings.get("degreed_base_url")
# baseurl
baseurl = "https://api." + degreed_base_url + "/"
# language
language = "en"
# get token
token = token_string.get_token_string()
# headers
headers = {"Authorization": "Bearer " + str(token)}


class RecommendSkillsTest(unittest.TestCase):
    """
    Given course data & status code
    test that a returning course by get_recommend_skills function have skills should match expected skills
    """
    @parameterized.expand([
        [200, {
            "links": {
                "self": "https://api.betatest.degreed.com/api/v2/content/zQV1pwa/skills"
            },
            "data": [{"type": "skills", "id": "Best Practices"}],
        }],
        [404, None]
    ])
    def test_get_recommend_skills_valid_course_id(self, status_code, expected):
        # set fake course data
        course = fake_course.get_data()
        # Mock 'requests' module 'get' method.
        mock_get_patcher = patch("lambda_function.requests.get")
        # Start patching 'requests.post'.
        mock_get = mock_get_patcher.start()
        # Configure the mock to return a response with status code 200.
        mock_get.return_value.status_code = status_code
        # Configure the mock to return a response with access token.
        mock_get.return_value.json.return_value = {
            "data": expected
        }
        # Call the function, which will send a request to the server.
        course = lambda_function.get_recommend_skills(baseurl, headers, course)
        # Stop patching 'requests'.
        mock_get_patcher.stop()
        # Assert that the request-response cycle completed successfully.
        self.assertEqual(expected, course.get("skills"))
