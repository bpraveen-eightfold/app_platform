from __future__ import absolute_import

import json
import unittest

from lambda_function import app_handler

class TestPersistContentApp(unittest.TestCase):

    def test_app_response_small_file(self):
        resp = app_handler(event={'trigger_name': 'position_export'}, context=None)
        self.assertIsNotNone(resp)

        body = resp.get('body', {})
        self.assertIsNotNone(body)

        data = json.loads(body)['data']
        self.assertEquals(data['actions'][0]['action_name'], 'persist_content')
        self.assertEquals(
            data['actions'][0]['request_data']['content'][0]['identifier'],
            'persist_content_data_small.xlsx'
        )
        self.assertIsNotNone(data['actions'][0]['request_data']['content'][0]['data'])
        self.assertLessEqual(
            len(data['actions'][0]['request_data']['content'][0]['data']), 7000
        )

    def test_app_response_med_file(self):
        resp = app_handler(
            event={
                'trigger_name': 'position_export',
                'app_settings': {
                    'file_size': 'med'
                }
            },
            context=None
        )
        self.assertIsNotNone(resp)

        body = resp.get('body', {})
        self.assertIsNotNone(body)

        data = json.loads(body)['data']
        self.assertEquals(data['actions'][0]['action_name'], 'persist_content')
        self.assertEquals(
            data['actions'][0]['request_data']['content'][0]['identifier'],
            'persist_content_data_med.xlsx'
        )
        self.assertIsNotNone(data['actions'][0]['request_data']['content'][0]['data'])
        self.assertLessEqual(
            len(data['actions'][0]['request_data']['content'][0]['data']), 450000
        )
