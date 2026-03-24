from __future__ import absolute_import

import unittest
from lambda_function import app_handler


class TestNectarHRLambdaFunction(unittest.TestCase):

    def test_app_url_return(self):
        event = {
            'trigger_name': 'careerhub_static_entity'
        }
        resp = app_handler(event, None)
        expected = {
            'statusCode': 200,
            'body': '{"app_url": "https://app.nectarhr.com/", "cache_ttl_seconds": 3600}',
        }
        self.assertEqual(resp, expected)

    def test_app_url_return_fail(self):
        event = {
            'trigger_name': 'not_careerhub_static_entity'
        }
        resp = app_handler(event, None)
        expected = {
            'statusCode': 500,
            'body': '{"error": "Unexpected trigger_name not_careerhub_static_entity"}',
        }
        self.assertEqual(resp, expected)
