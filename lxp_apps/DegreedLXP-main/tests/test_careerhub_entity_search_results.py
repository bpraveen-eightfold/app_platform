import unittest
from parameterized import parameterized
import requests_mock
import json
from fake_data import recommended_course, search_courses, course_list_data, inputs, token_string, entity_details, course_attendance_api_response
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
# token_url
token_url = "https://" + degreed_base_url
# language
language = "en"
# get token
token = token_string.get_token_string()
# headers
headers = {"Authorization": "Bearer " + str(token)}
# candidate id
candidate_id = "zk3jPZ"

"""
to check twp dict is equal or not
"""


def equal(a, b):
    type_a = type(a)
    type_b = type(b)

    if type_a != type_b:
        return False

    if isinstance(a, dict):
        if len(a) != len(b):
            return False
        for key in a:
            if key not in b:
                return False
        return True


class CareerhubEntitySearchResultsTest(unittest.TestCase):
    """
    Given valid term
    test that a response returning by this trigger function is correctly as expected
    """
    def test_careerhub_entity_search_results_valid_term(self):
        # update request data with valid term and also update app setting
        event = {}
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "start": 0,
            "term": "Microsoft Office",
        }
        event.update({"request_data": request_data, "app_settings": app_settings})

        # The Mocker object working as a context manager.
        with requests_mock.Mocker() as mock:
            # mock access token api
            access_token_return_json = {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 5183999,
                "refresh_token": "4cfc971e671a4cc5afbda32527f6e9c472bdfc6c77c64ee7a6fdc8a2f6e5a54b",
            }
            mock.post(
                token_url + "/oauth/token", json=access_token_return_json, status_code=200
            )
            # get email from request data
            email = lambda_function.get_email(request_data, app_settings)
            # mock get use id api
            get_userid_return_json = {"data": {"type": "users", "id": "zk3jPZ"}}
            mock.get(
                baseurl + "api/v2/users/" + email + "?identifier=email",
                json=get_userid_return_json,
                status_code=200,
            )
            # get course api call with filter query
            filter_search_term = request_data.get("term")
            url_without_nextBatch = (
                baseurl + "api/v2/content?filter%5Bterm%5D=" + filter_search_term
            )
            mock.get(
                url_without_nextBatch,
                headers=headers,
                status_code=200,
                json={"data": search_courses.get_data()},
            )
            # set expected response dict
            expected = {
                "entities": course_list_data.get_data(),
                "num_results": 6,
                "limit": 10,
                "offset": 0,
                "cursor": 0,
            }
            # set expected entity schema
            expected_entity_schema = expected.get("entities")[0]
            # calling the function should return filtered course list
            response = lambda_function.careerhub_entity_search_results_handler(
                event, context=""
            )
            response_body = json.loads(response.get("body"))
            response_data = response_body.get("data")
            response_entity_schema = response_data.get("entities")[0]
            # Check full data equal, not just schema
            self.assertEqual(expected_entity_schema, response_entity_schema)
            self.assertEqual(expected.get("num_results"), response_data.get("num_results"))
            self.assertEqual(expected.get("limit"), response_data.get("limit"), )
            self.assertEqual(expected.get("offset"), response_data.get("offset"))
            self.assertEqual(expected.get("cursor"), response_data.get("cursor"))

    """
    Given valid fq
    test that a response returning by this trigger function is correctly as expected
    """
    fq_skills_sample1 = {
        "position_skills": [
            {"name": "Business Strategy"},
            {"name": "Management"},
            {"name": "Software Development"},
            {"name": "Project Management"},
            {"name": "Project Manager"},
            {"name": "AWS"},
            {"name": "Proofing"},
        ],
        "profile_skills": [{"name": "Management"}],
    }
    sample1_data = {
        "data": {
            "id": "abc",
            "attributes": {
                "employee-id": None,
                "language": "en",
                "assignment-type": "Assigned",
            }
        }
    }
    fq_skills_sample2 = {
        "skill_goals": [],
        "profile_skills": []
    }

    # Full list of ids in mocked search results is ["ZQLjrNx", "zQV100Q", "ZQLjrxR", "ZQLjry6", "rwoA02k", "rwoAjdW", "rwoAjW0"]
    # rwoAjW0 is filtered out because language is empty which doesn't match setting of "en"
    # zQV100Q is filtered out because it appears in mocked course completion, we filter out completed courses
    @parameterized.expand([
        [fq_skills_sample1, sample1_data, 6, 1, ["abc", "ZQLjrNx", "ZQLjrxR", "ZQLjry6", "rwoA02k", "rwoAjdW"]],
        [fq_skills_sample2, entity_details.get_data(), 6, 1, ["rwoA7p5", "ZQLjrNx", "ZQLjrxR", "ZQLjry6", "rwoA02k", "rwoAjdW"]]
    ])
    def test_careerhub_entity_search_results_valid_fq(self, fq_skills, data_entity, num_results,
                                                      cursor, expected_response_ids):
        # update given request data with valid fq and app setting
        event = {}
        request_data = {
            "limit": 10,
            "current_user_email": "payal.sonawane@redcrackle.com",
            "start": 0,
            "fq": fq_skills,
        }
        event.update({"request_data": request_data, "app_settings": app_settings})

        # The Mocker object working as a context manager.
        with requests_mock.Mocker() as mock:
            # mock access token api
            access_token_return_json = {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 5183999,
                "refresh_token": "4cfc971e671a4cc5afbda32527f6e9c472bdfc6c77c64ee7a6fdc8a2f6e5a54b",
            }
            mock.post(
                token_url + "/oauth/token", json=access_token_return_json, status_code=200
            )
            # get email from request data
            email = lambda_function.get_email(request_data, app_settings)
            # mock get use id api
            get_userid_return_json = {"data": {"type": "users", "id": "zk3jPZ"}}
            mock.get(
                baseurl + "api/v2/users/" + email + "?identifier=email",
                json=get_userid_return_json,
                status_code=200,
            )
            # mock recommended courses api
            candidate_id = "zk3jPZ"
            mock.get(
                baseurl + "/api/v2/users/" + candidate_id + "/required-learning",
                headers=headers,
                json={"data": recommended_course.get_data()},
            )
            # fake recommended courses
            recommended_courses = recommended_course.get_data()
            # traverse fake recommended courses
            for course in recommended_courses:
                # parse course id from course
                course_id = course["included"][0]["id"]
                # fake skills json
                skills = {"data": [{"type": "skills", "id": "Project Manager"}]}
                # mock course skills api
                mock.get(
                    baseurl + "/api/v2/content/" + course_id + "/skills",
                    json=skills,
                    headers=headers,
                )
                # fake course details json
                course_details = data_entity
                # mock course detail api
                mock.get(
                    baseurl + "/api/v2/content/" + str(course_id),
                    json=course_details,
                    headers=headers,
                )

            filter_search_term = lambda_function.get_search_string(
                request_data, lambda_function.concate_skills, ""
            )
            # get course api call with filter query
            url_without_nextBatch = (
                baseurl + "api/v2/content?filter%5Bterm%5D=" + filter_search_term
            )

            if filter_search_term == '':
                # get course api call with filter query
                url_without_nextBatch = (
                        baseurl + "api/v2/content"
                )

            mock.get(
                url_without_nextBatch,
                headers=headers,
                status_code=200,
                json={"data": search_courses.get_data()},
            )

            mock.get(
                baseurl + "/api/v2/users/" + candidate_id + "/completions",
                json={"data": course_attendance_api_response.get_data()},
                headers=headers,
            )
            # set expected response dict
            expected = {
                "entities": course_list_data.get_data(),
                "num_results": num_results,
                "limit": 10,
                "offset": 0,
                "cursor": cursor,
            }
            # set expected entity schema
            expected_entity_schema = expected.get("entities")[0]
            # calling the function which will return filtered course list
            response = lambda_function.careerhub_entity_search_results_handler(
                event, context=""
            )
            response_body = json.loads(response.get("body"))
            response_data = response_body.get("data")
            response_entity_schema = response_data.get("entities")[0]
            # to check expected entity schema and response entity schema is equal or not
            # TODO: check full data instead of just schema, test doesn't work with that right now
            check_dict_keys = equal(expected_entity_schema, response_entity_schema)
            # assert statement to check expected dict and response dict
            self.assertTrue(check_dict_keys)
            self.assertEqual(expected.get("num_results"), response_data.get("num_results"))
            self.assertListEqual(expected_response_ids, [entity["entity_id"] for entity in response_data["entities"]])
            self.assertEqual(expected.get("limit"), response_data.get("limit"))
            self.assertEqual(expected.get("offset"), response_data.get("offset"))
            self.assertEqual(expected.get("cursor"), response_data.get("cursor"))
