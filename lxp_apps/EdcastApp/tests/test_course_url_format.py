import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa


class CourseUrlTest(unittest.TestCase):
    """
    Given url
    test that a returning string by course_url_format function should be matched with expected string
    """

    sample_url1 = "https://api.betatest.degreed.com/api/v2/content/?q=Proofing,Software Development"
    sample_url2 = (
        "https://api.betatest.degreed.com/api/v2/content/?q=" "&offset=0&limit=10"
    )

    @parameterized.expand(
        [
            [sample_url1, "https://api.betatest.degreed.com/api/v2/content/"],
            [
                sample_url2,
                "https://api.betatest.degreed.com/api/v2/content/?offset=0&limit=10",
            ],
        ]
    )
    def test_course_url_format_with_filter(self, arg1, expected):
        # set url
        url = arg1
        # calling the function which will return url without
        response_url = lambda_function.course_url_format(url)
        # to check expected url should be equal response url
        self.assertEqual(expected, response_url)
