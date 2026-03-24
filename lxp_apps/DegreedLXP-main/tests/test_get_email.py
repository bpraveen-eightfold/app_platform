import unittest
from parameterized import parameterized
from fake_data import inputs
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa

# user inputs
inputData = inputs.app()
# request data
request_data = inputData.get("request_data", {})
# app setting
app_settings = inputData.get("app_settings", {})


class EmailTest(unittest.TestCase):
    """
    Given email
    test that a returning email by get_email function should be matched expected value
    """
    @parameterized.expand([
        ["demo@degreed.com", True, "", "", "employee@email.com", "demo@degreed.com"],
        ["demo@degreed.com", False, "", "", "employee@email.com", "employee@email.com"],
        ["", True, "", "", "employee@email.com", ""],
        ["", False, "email@email.com", "", "", "email@email.com"],
        ["", False, "email@email.com", "user@email.com", "", "email@email.com"],
        ["", False, "", "user@email.com", "", "user@email.com"]
    ])
    def test_get_email_true_use_test_email(
            self, useTestEmail, boolean, email, currentUserEmail, employeeEmail, expected
    ):
        # update fake use_test_email in app settings
        app_settings = {
            "use_test_email": boolean,
            "degreed_test_email": useTestEmail,
        }
        # update fake use_test_email in request data
        request_data = {
            "employee_email": employeeEmail,
            "email": email,
            "current_user_email": currentUserEmail
        }
        # calling the function which will return email
        email = lambda_function.get_email(request_data, app_settings)
        # to check expected email is equal to email
        self.assertEqual(expected, email)
