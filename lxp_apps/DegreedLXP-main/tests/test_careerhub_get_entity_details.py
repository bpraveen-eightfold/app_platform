import unittest
from parameterized import parameterized
import requests_mock
import json
from fake_data import entity_details, inputs, token_string
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
to check two dict is equal or not
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


class CareerhubGetEntityDetailsTest(unittest.TestCase):
    """
    Given valid entity id
    test that a response returning by this trigger function is as expected
    """

    @parameterized.expand([
        ["rwoA7p5", 200, entity_details.get_final_entity_details()],
        ["xyz", 500, {"statusCode": 500, "body": 
            '{"error": "Could not get course detail. Status code: 500. Reason: None."}'}]
    ])
    def test_careerhub_get_entity_details_valid_entity_id(self, entity_id, status_code, expected):
        # update given request data with valid entity id
        event = {}
        request_data = {
            "current_user_email": "payal.sonawane@redcrackle.com",
            "entity_id": entity_id,
        }
        event.update({"request_data": request_data, "app_settings": app_settings})
        entity_id = request_data.get("entity_id", 0)

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

            # mock api to get entity details
            mock.get(
                baseurl + "/api/v2/content/" + str(entity_id),
                status_code=status_code,
                json=entity_details.get_data(),
                headers=headers,
            )
            # calling the function which will return entity details
            response = lambda_function.careerhub_get_entity_details_handler(
                event, context=""
            )
            if status_code == 200:
                response_body = json.loads(response.get("body"))
                response_data = response_body.get("data")
                # to check expected entity schema and response entity schema is equal or not
                check_dict_keys = equal(expected, response_data)
                self.assertTrue(check_dict_keys)
                self.assertEqual(expected.get("entity_id"), response_data.get("entity_id"))
            else:
                self.assertEqual(response.get("statusCode"), expected.get("statusCode"))
                self.assertEqual(response.get("body"), expected.get("body"))
