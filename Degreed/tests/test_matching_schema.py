import unittest
from parameterized import parameterized
import requests_mock
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


class MatchingSchemaTest(unittest.TestCase):
    """
    Given course
    test that a language returning by matching_schema function is equal as given language
    """
    @parameterized.expand([
        ["en", "en"],
        ["ku", ""],
        ["", "en"]
    ])
    def test_matching_schema_language_matched(self, lang, expected):
        # set fake course data
        course = fake_course.get_data()
        # get course id for getting course content details
        course_id = course["included"][0]["id"]

        with requests_mock.Mocker() as mock:
            mock.get(
                baseurl + "/api/v2/content/" + str(course_id),
                headers=headers,
                status_code=200,
                json={"data": {"type": "content", "id": course_id, "attributes": {"language": "en"}}},
            )
            response = lambda_function.matching_schema(baseurl, headers, course, lang)
            if response:
                response = response.get("attributes")["language"]
            self.assertEqual(expected, response)

    def test_course_language_matches_setting(self):
        self.assertTrue(lambda_function.course_language_matches_setting("en", "en"))
        self.assertTrue(lambda_function.course_language_matches_setting("en-US", "en"))
        self.assertFalse(lambda_function.course_language_matches_setting("fr", "en"))
        self.assertFalse(lambda_function.course_language_matches_setting("", "en"))
        self.assertFalse(lambda_function.course_language_matches_setting(None, "en"))

        # empty settings language should match everything
        self.assertTrue(lambda_function.course_language_matches_setting("en", ""))
        self.assertTrue(lambda_function.course_language_matches_setting("en-US", ""))
        self.assertTrue(lambda_function.course_language_matches_setting("fr", ""))
        self.assertTrue(lambda_function.course_language_matches_setting("", ""))
        self.assertTrue(lambda_function.course_language_matches_setting(None, ""))
