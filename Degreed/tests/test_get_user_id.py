import unittest
import requests_mock
from parameterized import parameterized
from fake_data import inputs, token_string
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa

inputData = inputs.app()
app_settings = inputData.get("app_settings", {})
request_data = inputData.get("request_data", {})
email = lambda_function.get_email(request_data, app_settings)
degreed_base_url = app_settings.get("degreed_base_url")
baseurl = "https://api." + degreed_base_url + "/"
language = app_settings.get("language", "en")
# get token
token = token_string.get_token_string()
request_headers = {"Authorization": "Bearer " + str(token)}


class UserIdTest(unittest.TestCase):
    """
    Given valid email
    test that a candidate_id returning by get_user_id function is equal as given fake candidate_id
    """
    @parameterized.expand([
        [email, 200, "zk3jPZ"],
        ["payal", 500, ""],
        ["", 500, ""],
    ])
    def test_get_user_id_valid_email(self, candidateEmail, status_code, expected):
        email = candidateEmail

        with requests_mock.Mocker() as mock:
            mock.get(
                baseurl + "api/v2/users/" + email + "?identifier=email",
                headers=request_headers,
                status_code=status_code,
                json={"data": {"type": "users", "id": "zk3jPZ"}},
            )
            candidate_id = lambda_function.get_user_id(email, baseurl, request_headers)
            self.assertEqual(expected, candidate_id)
