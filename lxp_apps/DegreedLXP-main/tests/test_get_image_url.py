import unittest
from parameterized import parameterized
from helper import resolve_app_path
resolve_app_path()
import lambda_function # noqa


class ImageUrlTest(unittest.TestCase):
    """
    Given url
    test that a response returning by get_image_url function should be equal to expected
    """
    @parameterized.expand([
        ["", "https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg"],
        [None, "https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg"],
        ["https://cdn2.goskills.com/blobs/blogs/126/12-hero.png",
         "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
        ["~/content/img/org/1420/6185f834-a940-4c0d-8338-a9572f6bb8b1.jpg",
         "https://prod.degreedcdn.com/content/img/org/1420/6185f834-a940-4c0d-8338-a9572f6bb8b1.jpg"]
    ])
    def test_get_image_url_empty(self, url, expected):
        # set empty url
        url = url
        # calling the function which will return url
        response = lambda_function.get_image_url(url, {})
        # to check response is equal to expected url
        self.assertEqual(expected, response)

    @parameterized.expand([
        ["", ""],
        [None, ""],
        ["https://cdn2.goskills.com/blobs/blogs/126/12-hero.png", ""],
    ])
    def test_get_image_url_skip_fall_back_image(self, url, expected):
        # set url
        url = url
        # calling the function with skip_fallback_image set to True which will return url
        response = lambda_function.get_image_url(url, {'skip_all_images': True})
        # to check response is equal to expected url
        self.assertEqual(expected, response)

    @parameterized.expand([
        ["", "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
        [None, "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
        ["https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg", "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
    ])
    def test_get_image_url_skip_fall_back_image_override_default(self, url, expected):
        # set url
        url = url
        # calling the function with skip_fallback_image set to True which will return url
        response = lambda_function.get_image_url(url, {'skip_all_images': True, 'default_image_url': "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"})
        # to check response is equal to expected url
        self.assertEqual(expected, response)

    @parameterized.expand([
        ["", "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
        [None, "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"],
        ["https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg", "https://blog.degreed.com/wp-content/themes/degreed-blog/assets/img/new-logo.svg"],
    ])
    def test_get_image_url_with_default(self, url, expected):
        # set url
        url = url
        # calling the function with skip_fallback_image set to True which will return url
        response = lambda_function.get_image_url(url, {'skip_all_images': False, 'default_image_url': "https://cdn2.goskills.com/blobs/blogs/126/12-hero.png"})
        # to check response is equal to expected url
        self.assertEqual(expected, response)
