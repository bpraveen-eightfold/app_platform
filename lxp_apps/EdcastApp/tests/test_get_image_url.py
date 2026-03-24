import unittest
from parameterized import parameterized
from helper import resolve_app_path

resolve_app_path()
import lambda_function  # noqa


class ImageUrlTest(unittest.TestCase):
    """
    Given url
    test that a response returning by get_image_url function should be equal to expected
    """

    @parameterized.expand(
        [
            ["", "https://integrations.edcast.com/assets/images/logo-icon.png"],
            [None, "https://integrations.edcast.com/assets/images/logo-icon.png"],
            [
                "https://ipac.page/images/brand-logo-1.jpg",
                "https://ipac.page/images/brand-logo-1.jpg",
            ],
        ]
    )
    def test_get_image_url_empty(self, url, expected):
        # set empty url
        url = url
        # calling the function which will return url
        response = lambda_function.get_image_url(url)
        # to check response is equal to expected url
        self.assertEqual(expected, response)
