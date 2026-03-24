from __future__ import absolute_import

import json
import unittest
from unittest import mock

import lambda_function

class TestFeedbackMessages(unittest.TestCase):
    def setUp(self):
        self.event = {
            "trigger_name": "feedback_requested",
            "request_data": {
                "candidateProfileReviewer": {
                    "encId": "rOBZEwy3",
                    "title": "",
                    "skills": [
                        "\"Sales\"  Management",
                        "\"\"Account\"\" Management",
                        "Visualization",
                        "Major Account",
                        "ERP",
                        "New Accounts",
                        "Human Resources",
                        "Human Capital Management",
                        "SAP",
                        "Telecommunications"
                    ],
                    "workExperienceYears": 32.416666666666664,
                    "experiences": [
                        {
                            "work": "Corporate Visions \"Whiteboard\" Selling",
                            "durationMonths": 1,
                            "title": "Sr. Hadoop\\\u200bBig Data Engineer at Microsoft"
                        },
                        {
                            "work": "Microsoft",
                            "durationMonths": 85,
                            "title": "Sr. Hadoop\\Big Data Engineer"
                        },
                        {
                            "work": "ADP",
                            "durationMonths": 99,
                            "title": "Major Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive"
                        }
                    ],
                    "location": "\"Dallas\", TX, United States",
                    "profileId": 68794839659,
                    "fullName": "\"Mike\" Barry",
                    "email": "mikepatrickbarry@gmail.com"
                },
                "feedbackId": 68720333606,
                "position": {
                    "positionId": 68726765095,
                    "name": "\"Strategic\" Account Executive, West"
                },
                "viewFeedbackUrl": "https://employee.eightfold.ai/profile/rOBZEwy3?activeTab=interviewnote_hm_feedback&pid=68726765095&feedbackId=z1qM9NzZ",
                "feedbackUrl": "https://employee.eightfold.ai/v2/interview_feedback/z1qM9NzZ",
                "candidateProfileRequester": {
                    "encId": "rOBZEwy3",
                    "title": "",
                    "skills": [
                        "\"Sales\"  Management",
                        "\"\"Account\"\" Management",
                        "Visualization",
                        "Major Account",
                        "ERP",
                        "New Accounts",
                        "Human Resources",
                        "Human Capital Management",
                        "SAP",
                        "Telecommunications"
                    ],
                    "workExperienceYears": 32.416666666666664,
                    "experiences": [
                        {
                            "work": "Corporate Visions \"Whiteboard\" Selling",
                            "durationMonths": 1,
                            "title": "Sr. Hadoop\\\u200bBig Data Engineer at Microsoft"
                        },
                        {
                            "work": "Microsoft",
                            "durationMonths": 85,
                            "title": "Sr. Hadoop\\Big Data Engineer"
                        },
                        {
                            "work": "ADP",
                            "durationMonths": 99,
                            "title": "Major Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive"
                        }
                    ],
                    "location": "\"Dallas\", TX, United States",
                    "profileId": 68794839659,
                    "fullName": "\"Mike\" Barry",
                    "email": "mikepatrickbarry@gmail.com"
                },
                "requester": {
                    "fullName": "\"Tess\" Johnson",
                    "slackTokens": [
                        "xoxb-dummy-token"
                    ],
                    "email": "ashrivastava@eightfold.ai",
                    "domain": "employee.eightfold.ai",
                    "redirectEmail": None
                },
                "reviewer": {
                    "fullName": "\"Dave\" Carpini",
                    "slackTokens": [
                        "xoxb-dummy-token"
                    ],
                    "email": "ashrivastava@eightfold.ai",
                    "domain": "employee.eightfold.ai",
                    "redirectEmail": None
                },
                "reminderCount": 0
            }
        }

    @mock.patch('lambda_function._send_slack_message')
    @mock.patch('lambda_function.get_slack_user_by_email')
    def test_feedback_messages_and_templates(self, mock_get_slack_user_by_email, mock__send_slack_message):
        feedback_triggers = ['feedback_requested', 'feedback_submitted', 'feedback_reminder', 'feedback_cancelled']
        mock_get_slack_user_by_email.return_value = {'user': {'id': 'U023LB8LX5Z'}}
        mock__send_slack_message.return_value = {'ok': True, 'channel': 'D02BABFN128', 'ts': '1634113407.001100', 'message': {'bot_id': 'B02AWPCFC6S', 'type': 'message', 'text': '"Tess" Johnson has requested feedback for the candidate "Mike" Barry ', 'user': 'U02BT4X8U9W', 'ts': '1634113407.001100', 'team': 'T1UL59A9M', 'bot_profile': {'id': 'B02AWPCFC6S', 'app_id': 'A02AZTJR93M', 'name': 'Eightfold-demo', 'icons': {'image_36': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_36.jpg', 'image_48': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_48.jpg', 'image_72': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_72.jpg'}, 'deleted': False, 'updated': 1630041650, 'team_id': 'T1UL59A9M'}, 'blocks': [{'type': 'section', 'block_id': 'q=WZT', 'text': {'type': 'plain_text', 'text': 'Hello "Dave" Carpini', 'emoji': True}}, {'type': 'section', 'block_id': '1Ep', 'text': {'type': 'plain_text', 'text': 'Please click the Provide Feedback button below to review the candidate profile and leave a quick feedback.', 'emoji': True}}, {'type': 'section', 'block_id': '0=21', 'text': {'type': 'mrkdwn', 'text': '*Position*: "Strategic" Account Executive, West', 'verbatim': False}}, {'type': 'section', 'block_id': 'w/d', 'text': {'type': 'mrkdwn', 'text': 'Thanks,\n"Tess" Johnson', 'verbatim': False}}, {'type': 'divider', 'block_id': 'AM6y/'}, {'type': 'section', 'block_id': 'B7VpJ', 'text': {'type': 'mrkdwn', 'text': '<https://employee.eightfold.ai/profile/rOBZEwy3?back=/interview_feedback/&pid=68726765095|*"Mike" Barry*>\n\n"Dallas", TX, United States', 'verbatim': False}}, {'type': 'section', 'block_id': '1NpJ', 'text': {'type': 'mrkdwn', 'text': '*32 Years Experience* \nSr. Hadoop\\\u200bBig Data Engineer at Microsoft, Corporate Visions "Whiteboard" Selling 1 Months\nSr. Hadoop\\Big Data Engineer, Microsoft 7 Years\nMajor Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive, ADP 8 Years', 'verbatim': False}}, {'type': 'section', 'block_id': 'S0C', 'text': {'type': 'mrkdwn', 'text': '*Skills:*\n"Sales"  Management, ""Account"" Management, Visualization, Major Account, ERP, New Accounts, Human Resources, Human Capital Management, SAP, Telecommunications', 'verbatim': False}}, {'type': 'divider', 'block_id': 'bW1G'}, {'type': 'actions', 'block_id': 'TK6J', 'elements': [{'type': 'button', 'action_id': 'feedback_requested_button', 'text': {'type': 'plain_text', 'text': 'Provide Feedback', 'emoji': True}, 'style': 'primary', 'url': 'https://employee.eightfold.ai/v2/interview_feedback/z1qM9NzZ?messenger=slack'}]}]}}
        expected_actions = [{'action_name': 'add_user_message', 'request_data': {'conversationType': 'slack', 'conversationId': 'feedback_requested', 'messageData': {'slack_message_blocks': [{'type': 'section', 'text': {'type': 'plain_text', 'text': 'Hello "Dave" Carpini'}}, {'type': 'section', 'text': {'type': 'plain_text', 'text': 'Please click the Provide Feedback button below to review the candidate profile and leave a quick feedback.'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Position*: "Strategic" Account Executive, West'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': 'Thanks,\n"Tess" Johnson'}}, {'type': 'divider'}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '<https://employee.eightfold.ai/profile/rOBZEwy3?back=/interview_feedback/&pid=68726765095|*"Mike" Barry*>\n\n"Dallas", TX, United States'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*32 Years Experience* \nSr. Hadoop\\\u200bBig Data Engineer at Microsoft, Corporate Visions "Whiteboard" Selling 1 Months\nSr. Hadoop\\Big Data Engineer, Microsoft 7 Years\nMajor Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive, ADP 8 Years'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Skills:*\n"Sales"  Management, ""Account"" Management, Visualization, Major Account, ERP, New Accounts, Human Resources, Human Capital Management, SAP, Telecommunications'}}, {'type': 'divider'}, {'type': 'actions', 'elements': [{'type': 'button', 'text': {'type': 'plain_text', 'text': 'Provide Feedback'}, 'style': 'primary', 'url': 'https://employee.eightfold.ai/v2/interview_feedback/z1qM9NzZ?messenger=slack', 'action_id': 'feedback_requested_button'}]}], 'data': {'profile_feedback_id': 68720333606, 'reminder_number': 0}}, 'emailTo': 'U023LB8LX5Z', 'emailFrom': 'T1UL59A9M_A02AZTJR93M', 'company': 'ashrivastava@eightfold.ai', 'profileId': 68794839659, 'positionId': 68726765095, 'failureTime': 0, 'failureReason': None, 'deliveryTime': 1634113407}}]
        event = self.event

        resp = lambda_function.app_handler(event=event, context={})
        assert resp.get('statusCode') == 200
        assert json.loads(resp.get('body')).get('data').get('actions') == expected_actions

        for trigger in feedback_triggers:
            event['trigger_name'] = trigger
            resp = lambda_function.app_handler(event=event, context={})
            assert resp.get('statusCode') == 200

    @mock.patch('lambda_function._send_slack_message')
    @mock.patch('lambda_function.get_slack_user_by_email')
    def test_send_message_failure(self, mock_get_slack_user_by_email, mock__send_slack_message):
        mock_get_slack_user_by_email.return_value = {'user': {'id': 'U023LB8LX5Z'}}
        mock__send_slack_message.return_value = {'ok': False, 'error': 'invalid_auth'}
        expected_actions = [{'action_name': 'add_user_message', 'request_data': {'conversationType': 'slack', 'conversationId': 'feedback_requested', 'messageData': {'slack_message_blocks': [{'type': 'section', 'text': {'type': 'plain_text', 'text': 'Hello "Dave" Carpini'}}, {'type': 'section', 'text': {'type': 'plain_text', 'text': 'Please click the Provide Feedback button below to review the candidate profile and leave a quick feedback.'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Position*: "Strategic" Account Executive, West'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': 'Thanks,\n"Tess" Johnson'}}, {'type': 'divider'}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '<https://employee.eightfold.ai/profile/rOBZEwy3?back=/interview_feedback/&pid=68726765095|*"Mike" Barry*>\n\n"Dallas", TX, United States'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*32 Years Experience* \nSr. Hadoop\\\u200bBig Data Engineer at Microsoft, Corporate Visions "Whiteboard" Selling 1 Months\nSr. Hadoop\\Big Data Engineer, Microsoft 7 Years\nMajor Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive, ADP 8 Years'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Skills:*\n"Sales"  Management, ""Account"" Management, Visualization, Major Account, ERP, New Accounts, Human Resources, Human Capital Management, SAP, Telecommunications'}}, {'type': 'divider'}, {'type': 'actions', 'elements': [{'type': 'button', 'text': {'type': 'plain_text', 'text': 'Provide Feedback'}, 'style': 'primary', 'url': 'https://employee.eightfold.ai/v2/interview_feedback/z1qM9NzZ?messenger=slack', 'action_id': 'feedback_requested_button'}]}], 'data': {'profile_feedback_id': 68720333606, 'reminder_number': 0}}, 'emailTo': 'U023LB8LX5Z', 'emailFrom': 'None_None', 'company': 'ashrivastava@eightfold.ai', 'profileId': 68794839659, 'positionId': 68726765095, 'failureTime': 1634118411, 'failureReason': 'invalid_auth', 'deliveryTime': 0}}]
        event = self.event

        resp = lambda_function.app_handler(event=event, context={})
        assert resp.get('statusCode') == 200
        resp_actions = json.loads(resp.get('body')).get('data').get('actions')
        resp_actions[0]['request_data']['failureTime'] = expected_actions[0]['request_data']['failureTime']
        assert resp_actions == expected_actions

    @mock.patch('lambda_function._send_slack_message')
    @mock.patch('lambda_function.get_slack_user_by_email')
    def test_get_slack_user_failure(self, mock_get_slack_user_by_email, mock__send_slack_message):
        mock_get_slack_user_by_email.return_value = {'ok': False, 'error': 'users_not_found'}
        mock__send_slack_message.return_value = {}
        expected_actions = [{'action_name': 'add_user_message', 'request_data': {'conversationType': 'slack', 'conversationId': 'feedback_requested', 'messageData': [{'type': 'section', 'text': {'type': 'plain_text', 'text': 'Hello "Dave" Carpini'}}, {'type': 'section', 'text': {'type': 'plain_text', 'text': 'Please click the Provide Feedback button below to review the candidate profile and leave a quick feedback.'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Position*: "Strategic" Account Executive, West'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': 'Thanks,\n"Tess" Johnson'}}, {'type': 'divider'}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '<https://employee.eightfold.ai/profile/rOBZEwy3?back=/interview_feedback/&pid=68726765095|*"Mike" Barry*>\n\n"Dallas", TX, United States'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*32 Years Experience* \nSr. Hadoop\\\u200bBig Data Engineer at Microsoft, Corporate Visions "Whiteboard" Selling 1 Months\nSr. Hadoop\\Big Data Engineer, Microsoft 7 Years\nMajor Account Salesperson, Mid-Market Sales Manager, Sales Training Manager and Senior Account Executive, ADP 8 Years'}}, {'type': 'section', 'text': {'type': 'mrkdwn', 'text': '*Skills:*\n"Sales"  Management, ""Account"" Management, Visualization, Major Account, ERP, New Accounts, Human Resources, Human Capital Management, SAP, Telecommunications'}}, {'type': 'divider'}, {'type': 'actions', 'elements': [{'type': 'button', 'text': {'type': 'plain_text', 'text': 'Provide Feedback'}, 'style': 'primary', 'url': 'https://employee.eightfold.ai/v2/interview_feedback/z1qM9NzZ?messenger=slack', 'action_id': 'feedback_requested_button'}]}], 'emailTo': 'None', 'emailFrom': 'None_None', 'company': 'ashrivastava@eightfold.ai', 'profileId': 68794839659, 'positionId': 68726765095, 'failureTime': 1634119348, 'failureReason': 'users_not_found', 'deliveryTime': 0}}]
        event = self.event

        resp = lambda_function.app_handler(event=event, context={})
        assert resp.get('statusCode') == 200
        resp_actions = json.loads(resp.get('body')).get('data').get('actions')
        resp_actions[0]['request_data']['failureTime'] = expected_actions[0]['request_data']['failureTime']
        assert resp_actions == expected_actions
        
    @mock.patch('lambda_function.send_slack_messages')
    def test_send_approval_request(self, mock_send_slack_messages):
        event = {
            "trigger_name": "t3s_approval_workflow_notification",
            "request_data": {
                    "receivers": [
                    {
                        "slack_tokens": [
                        "xoxb-dummy-token",
                        "xoxb-dummy-token"
                        ],
                        "email": "test@eightfold.ai",
                        "message_blocks": [
                        {
                            "type": "section",
                            "text": {
                            "type": "mrkdwn",
                            "text": "hi kaylie,\n\nyour approval is requested to make an offer to <https://app.eightfold.ai/profile-v2/dummy| *greg lee, cpa*>\n"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "approve"
                                },
                                "style": "primary",
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=approve"
                            },
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "reject"
                                },
                                "style": "danger",
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=reject"
                            },
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "comment"
                                },
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=comment"
                            }
                            ]
                        }
                        ],
                        "notif_text": "[action needed] - offer approval request greg lee, cpa"
                    },
                    {
                        "slack_tokens": [
                        "xoxb-dummy-token",
                        "xoxb-dummy-token"
                        ],
                        "email": "test2@eightfold.ai",
                        "message_blocks": [
                        {
                            "type": "section",
                            "text": {
                            "type": "mrkdwn",
                            "text": "hi abel,\n\nyour approval is requested to make an offer to <https://app.eightfold.ai/profile-v2/dummy| *greg lee, cpa*>\n"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "approve"
                                },
                                "style": "primary",
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=approve"
                            },
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "reject"
                                },
                                "style": "danger",
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=reject"
                            },
                            {
                                "type": "button",
                                "text": {
                                "type": "plain_text",
                                "text": "comment"
                                },
                                "url": "https://app.eightfold.ai/approval/dashboard/offer/dummy?action=comment"
                            }
                            ]
                        }
                        ],
                        "notif_text": "[action needed] - offer approval request greg lee, cpa"
                    }
                ]
            }, 
            "app_settings": {
                "secrets": {}
            }
        }
        
        mock_send_slack_messages.return_value = {'ok': True, 'channel': 'dummy', 'ts': '1634111121.000700'}
        resp = lambda_function.app_handler(event=event, context={})
        assert resp.get('statusCode') == 200
        assert json.loads(resp.get('body')).get('data').get('actions') == [{'ok': True, 'channel': 'dummy', 'ts': '1634111121.000700'}, {'ok': True, 'channel': 'dummy', 'ts': '1634111121.000700'}]


class TestWelcomeMessage(unittest.TestCase):
    def setUp(self):
        self.event = {
            "trigger_name": "messenger_app_interaction",
            "request_data": {
                "messenger_app_data": {
                    "bot_token": "xoxb-dummy-token",
                    "team_id": "T1UL59A9M",
                    "user_id": "U023LB8LX5Z",
                    "app_id": "A02AZTJR93M"
                }
            }
        }

    @mock.patch('lambda_function._send_slack_message')
    @mock.patch('lambda_function.get_user_info_by_id')
    def test_send_welcome_message(self, mock_get_user_info_by_id, mock__send_slack_message):
        mock_get_user_info_by_id.return_value = {'user': {'profile': {'email': 'ashrivastava@eightfold.ai'}}}
        mock__send_slack_message.return_value = {'ok': True, 'channel': 'D02BABFN128', 'ts': '1634111121.000700',
         'message': {'bot_id': 'B02AWPCFC6S', 'type': 'message', 'text': 'Welcome to the Eightfold Slack App! ', 'user': 'U02BT4X8U9W',
                     'ts': '1634111047.000700', 'team': 'T1UL59A9M',
                     'bot_profile': {'id': 'B02AWPCFC6S', 'app_id': 'A02AZTJR93M', 'name': 'Eightfold-demo',
                                     'icons': {'image_36': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_36.jpg',
                                               'image_48': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_48.jpg',
                                               'image_72': 'https://avatars.slack-edge.com/2021-08-18/2377993258823_2688cd1f0b3f4ca1f5ae_72.jpg'},
                                     'deleted': False, 'updated': 1630041650, 'team_id': 'T1UL59A9M'}, 'blocks': [
                 {'type': 'section', 'block_id': '9dr+V', 'text': {'type': 'plain_text', 'text': 'Welcome to the Eightfold Slack App!', 'emoji': True}},
                 {'type': 'section', 'block_id': 'mdTe8',
                  'text': {'type': 'plain_text', 'text': 'You will be receiving all Eightfold notifications through this app.', 'emoji': True}}]}}

        expected_actions = [{'action_name': 'add_user_message', 'request_data': {'conversationType': 'slack', 'conversationId': 'messenger_app_interaction', 'messageData': [{'type': 'section', 'text': {'type': 'plain_text', 'text': 'Welcome to the Eightfold Slack App!'}}, {'type': 'section', 'text': {'type': 'plain_text', 'text': 'You will be receiving all Eightfold notifications through this app.'}}], 'emailTo': 'U023LB8LX5Z', 'emailFrom': 'T1UL59A9M_A02AZTJR93M', 'company': 'ashrivastava@eightfold.ai', 'profileId': None, 'positionId': None, 'failureTime': 0, 'failureReason': None, 'deliveryTime': 1634111047}}]

        event = self.event
        resp = lambda_function.app_handler(event=event, context={})
        assert resp.get('statusCode') == 200
        assert json.loads(resp.get('body')).get('data').get('actions') == expected_actions
