import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa


class DateFormatTest(unittest.TestCase):
    """
    Given datetime
    test that a response returning by get_date function is equal as expected
    """

    @parameterized.expand(
        [
            ["2020-03-23T10:28:43.000Z", "23/03/2020"],
            ["2022-04-20T20:41:20", "20/04/2022"],
            ["", ""],
            ["2022-02", "2022-02"],
        ]
    )
    def test_get_date(self, arg1, expected):
        # set datatime
        datetime = arg1
        # calling the function which will return date
        response = lambda_function.get_date(datetime)
        # to check response should be equal to expected
        self.assertEqual(expected, response)
