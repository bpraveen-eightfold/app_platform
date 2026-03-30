import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class TimeEpochTest(unittest.TestCase):
    """
    Given date
    test that a response returning by time_epoch function is equal as expected
    """

    @parameterized.expand([
        ["2022-02-16T20:41:20.413", 1645044080],
        ["2022-04-20T20:41:20", 1650487280],
        ["", None],
        ["2022-02", "2022-02"]
    ])
    def test_time_epoch_valid_date(self, datetime, expected):
        # set data
        date = datetime
        # set expected
        expected = expected
        # calling the function which will return date timestamp
        response = lambda_function.time_epoch(date)
        # to check response should be equal to expected
        self.assertEqual(expected, response)
