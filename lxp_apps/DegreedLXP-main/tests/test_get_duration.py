import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class DurationTest(unittest.TestCase):
    """
    Given duration
    test that a response returning by get_duration function is equal to expected value
    """
    @parameterized.expand([
        ["seconds", 3600, 1],
        ["minutes", 120, 2],
        ["words", 15000, 1],
        ["", None, "NA"]
    ])
    def test_get_duration(self, duration_type, duration, expected):
        duration_type = duration_type
        # set fake duration
        duration = duration
        # calling the function which will return value in hours
        response = lambda_function.get_duration(duration_type, duration)
        # to check response should be equal to expected
        self.assertEqual(expected, response)
