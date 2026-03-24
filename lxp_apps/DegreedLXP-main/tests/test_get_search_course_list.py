import unittest
from parameterized import parameterized
from unittest.mock import patch
import requests_mock
from urllib.parse import quote_plus
from fake_data import search_courses, inputs, token_string
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
# skills sample
skills = [
    {"name": "Business Strategy"},
    {"name": "Management"},
    {"name": "Software Development"},
    {"name": "AWS"},
    {"name": "Proofing"}
]
# Profile skills
profile_skills = [{"name": "Management"}]


class SearchCourseListTest(unittest.TestCase):
    """
    Given skills and profile skills
    test that a course list returning by get_search_course_list function is correctly
    """
    @parameterized.expand([
        [{"required_skills": skills, "profile_skills": profile_skills}],
        [{"project_skills": skills, "profile_skills": profile_skills}],
        [{"skill_goals": skills, "profile_skills": profile_skills}],
        [{"position_skills": skills, "profile_skills": profile_skills}]
    ])
    def test_get_search_course_list_based_on_profile_and_required_skills(self, fq_skills):
        # set fake required_skills and profile_skills
        fq = fq_skills
        # update fake required and profile skills in request data
        request_data.update({"fq": fq, "term": ""})
        fake_data_course_len = 0
        # count matched course with given language
        for course in search_courses.get_data():
            if course["attributes"]["language"] == language:
                fake_data_course_len = fake_data_course_len + 1

        with requests_mock.Mocker() as mock:
            filter_search_term = lambda_function.get_search_string(
                request_data, lambda_function.concate_skills, ""
            )
            url_without_nextBatch = (
                baseurl + "api/v2/content?filter%5Bterm%5D=" + quote_plus(filter_search_term)
            )
            mock.get(
                url_without_nextBatch,
                headers=headers,
                status_code=200,
                json={"data": search_courses.get_data()},
            )
            mock.get(
                baseurl + "/api/v2/users/abc/completions",
                json={"data": []},
                headers=headers,
            )
            # Call the function, which will send a request to the server.
            response = lambda_function.get_search_course_list(
                baseurl, headers, language, request_data, "abc", {}
            )
        # Assert that the request-response cycle completed successfully.
        self.assertEqual(fake_data_course_len, response.get("course_len"))

    @parameterized.expand([
        [{"not_internal_only": True}, {'filter[term]': 'test term', 'filter[internal_only]': 'false'}],
        [{"include_restricted": True}, {'filter[term]': 'test term', 'filter[include_restricted]': 'true'}],
        [{"include_restricted": True, "not_internal_only": True},
            {'filter[term]': 'test term', 'filter[internal_only]': 'false', 'filter[include_restricted]': 'true'}],
    ])
    def test_get_search_course_list_params(self, app_settings, expected_params):
        request_data.update({"term": "test term", "fq": []})

        with patch('lambda_function.requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            # Configure the mock to return a response with access token.
            mock_get.return_value.json.return_value = {"data": search_courses.get_data()}
            # Call the function, which will send a request to the server.
            response = lambda_function.get_search_course_list(
                baseurl, headers, language, request_data, "abc", app_settings
            )
            mock_get.assert_called_once_with(f'{baseurl}api/v2/content', params=expected_params, headers=headers)
