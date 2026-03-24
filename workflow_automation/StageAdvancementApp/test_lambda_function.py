import unittest

import lambda_function


class TestAppHandler(unittest.TestCase):

    def setUp(self):
        self.app_settings = {
            "pre_condition": "{{application_stage in [\"recruiter screen\", \"HM Screen\"]}}",
            "rules": [
                {
                    "current_stages": ["recruiter screen"],
                    "previous_stages": ['resume screen'],
                    "notification_templates": [
                        {
                            "template_name": "recruiter_screen_scheduling_template",
                            "email_to": "{{candidateProfile.email}}",
                            "email_from": "demo@test.com", 
                            "template_type": "email_template",
                            "reply_to": "demo@test.com",
                        }
                    ],
                },
                {
                    "current_stages": ["HM screen"],
                    "notification_templates": [
                        {
                            "template_name": "some_name",
                            "email_to": "{{candidateProfile.email}}",
                            "email_from": "demo@test.com",
                            "template_type": "scheduling_template",
                            "reply_to": "demo@test.com",

                        }
                    ],
                },
                {
                    "current_stages": ["face screen"],
                    "notification_templates": [
                        {
                            "template_name": "some_name",
                            "email_to": "{{candidateProfile.email}}",
                            "email_from": "demo@test.com",
                            "template_type": "whatsapp_template",
                            "reply_to": "demo@test.com",

                        }
                    ],
                }
            ],
            "request_data": ["stage", "candidateProfile.email",  "candidateProfile.profileId", "position.positionId", "groupId"],
            "request_data_previous": ['stage'],
        }

        self.request_data = {
            'stage': "recruiter screen",
            'groupId': 'test.com',
            'previous': {
                'stage': 'resume screen'
            },
            'candidateProfile': {
                'email': 'abs@test.com',
                'profileId': 123
            },
            'position': {
                'positionId': 321
            }
        }

    def trigger_lambda(self):
        resp = lambda_function.app_handler(event={
                'app_settings': self.app_settings,
                'request_data': self.request_data
            }, context=None)
        actions = resp.get('body', {}).get('data', {}).get('actions', [])
        return actions

    def test_successful_run(self):
        actions = self.trigger_lambda()
        assert len(actions) == 1

    def test_previous_stages_not_specified(self):
        self.request_data['stage'] = 'HM screen'
        actions = self.trigger_lambda()
        assert len(actions) == 1

    def test_application_stage_not_matched(self):
        self.request_data['stage'] = 'Not available screen'
        self.trigger_lambda = self.trigger_lambda()
        actions = self.trigger_lambda
        assert len(actions) == 0
