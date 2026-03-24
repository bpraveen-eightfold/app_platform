import unittest
from parameterized import parameterized
from unittest.mock import patch
from fake_data import search_courses, inputs, token_string
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})
# edcast baseurl
edcast_base_url = app_settings.get("edcast_base_url")
# email
email = app_settings.get("edcast_test_email")
# baseurl
baseurl = "https://api." + edcast_base_url + "/"
# language
language = "en"
# get token
token = token_string.get_token_string()
# api key
api_key = app_settings.get("edcast_api_key")
# headers
headers = {
    "X-API-KEY": api_key,
    "X-ACCESS-TOKEN": token,
    "Content-Type": "application/json",
}
# skills sample
skills = [
    {"name": "Business Strategy"},
    {"name": "Management"},
    {"name": "Software Development"},
    {"name": "AWS"},
    {"name": "Proofing"},
]
# Profile skills
profile_skills = [{"name": "Management"}]


class SearchCourseListTest(unittest.TestCase):
    """
    Given skills and profile skills
    test that a course list returning by get_search_course_list function is correctly
    """

    @parameterized.expand(
        [
            [{"required_skills": skills, "profile_skills": profile_skills}, 200],
            [{"project_skills": skills, "profile_skills": profile_skills}, 200],
            [{"skill_goals": skills, "profile_skills": profile_skills}, 200],
            [{"position_skills": skills, "profile_skills": profile_skills}, 200],
            [{"position_skills": skills}, 500],
            [{"profile_skills": profile_skills}, 404],
        ]
    )
    def test_get_course_list(self, fq_skills, status_code):
        # set fake required_skills and profile_skills
        fq = fq_skills
        # update fake required and profile skills in request data
        request_data.update({"fq": fq, "term": ""})
        fake_data_course_len = 0
        # count matched course with given language
        for course in search_courses.get_data():
            if course["language"] == language:
                fake_data_course_len = fake_data_course_len + 1

        # Mock 'requests' module 'get' method.
        mock_get_patcher = patch("lambda_function.requests.get")
        # Start patching 'requests.post'.
        mock_get = mock_get_patcher.start()
        # Configure the mock to return a response with status code 200.
        mock_get.return_value.status_code = status_code
        # Configure the mock to return a response with access token.
        mock_get.return_value.json.return_value = {"cards": search_courses.get_data()}
        # Call the function, which will send a request to the server.
        response = lambda_function.get_course_list(
            baseurl, headers, email, language, request_data, 0, 10
        )
        print(response)
        # Stop patching 'requests'.
        mock_get_patcher.stop()
        # Assert that the request-response cycle completed successfully.
        if status_code != 200:
            self.assertEqual(0, response.get("course_len"))
        else:
            self.assertEqual(fake_data_course_len, response.get("course_len"))
