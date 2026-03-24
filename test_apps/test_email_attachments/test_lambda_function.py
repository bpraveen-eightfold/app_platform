from __future__ import absolute_import

import json
import unittest

from lambda_function import app_handler


RECRUITER_EMAIL = 'test@example.com'
SUBJECT = 'Test Email Attachments'
BODY = 'Test email attachments'
IDENTIFIER = 'example-attachment.csv'
ENCODING = 'base64'
TEMPLATE_CATEGORY = 'contact'
TEMPLATE_NAME = 'Outreach Template 1'

class TestTestEmailAttachmentsApp(unittest.TestCase):

    def checkAttachment(self, data):
        self.assertEqual(
            data['actions'][0]['request_data']['attachments'][0]['identifier'],
            IDENTIFIER
        )
        self.assertIsNotNone(data['actions'][0]['request_data']['attachments'][0]['data'])
        self.assertEqual(
            data['actions'][0]['request_data']['attachments'][0]['encoding'],
            ENCODING
        )

    def test_send_email_action_response(self):
        resp = app_handler(
            event={
                'trigger_name': 'position_export',
                'request_data': {
                    'recruiter_email': RECRUITER_EMAIL
                },
                'app_settings': {
                    'is_email_with_template': False,
                },
            }, 
            context=None
        )
        self.assertIsNotNone(resp)

        body = resp.get('body', {})
        self.assertIsNotNone(body)

        data = json.loads(body)['data']
        self.assertEqual(data['actions'][0]['action_name'], 'send_email')
        self.assertEqual(
            data['actions'][0]['request_data']['email_from'],
            RECRUITER_EMAIL
        )
        self.assertEqual(
            data['actions'][0]['request_data']['email_to'],
            RECRUITER_EMAIL
        )
        self.assertEqual(
            data['actions'][0]['request_data']['subject'],
            SUBJECT
        )
        self.assertEqual(
            data['actions'][0]['request_data']['body'],
            BODY
        )
        self.checkAttachment(data)

    def test_send_email_with_template_v2_action_response(self):
        resp = app_handler(
            event={
                'trigger_name': 'position_export',
                'request_data': {
                    'recruiter_email': RECRUITER_EMAIL
                },
                'app_settings': {
                    'is_email_with_template': True,
                },
            }, 
            context=None
        )
        self.assertIsNotNone(resp)

        body = resp.get('body', {})
        self.assertIsNotNone(body)

        data = json.loads(body)['data']
        self.assertEqual(data['actions'][0]['action_name'], 'send_email_with_template_v2')
        self.assertEqual(
            data['actions'][0]['request_data']['emailFrom'],
            RECRUITER_EMAIL
        )
        self.assertEqual(
            data['actions'][0]['request_data']['replyTo'],
            RECRUITER_EMAIL
        )
        self.assertEqual(
            data['actions'][0]['request_data']['emailTo'],
            RECRUITER_EMAIL
        )
        self.assertEqual(
            data['actions'][0]['request_data']['templateCategory'],
            TEMPLATE_CATEGORY
        )
        self.assertEqual(
            data['actions'][0]['request_data']['templateName'],
            TEMPLATE_NAME
        )
        self.checkAttachment(data)
