# pylint: disable=ef-restricted-imports, unused-variable, unused-import

"""
    - Include all dependencies such as Python Standard Modules and open source libraries
"""
from __future__ import absolute_import

import os
import time
import json

import traceback2
import requests
import message_builder

SLACK_LOOKUP_BY_EMAIL_API_URL = "https://slack.com/api/users.lookupByEmail"
SLACK_CHAT_POST_MESSAGE_API_URL = "https://slack.com/api/chat.postMessage"
SLACK_USER_INFO_API_URL = "https://slack.com/api/users.info"
ADD_USER_MESSAGE_ACTION = 'add_user_message'
WELCOME_MESSAGE_TRIGGER_NAME = 'messenger_app_interaction'
T3S_APPROVAL_WORKFLOW_NOTIFICATION = 't3s_approval_workflow_notification'
EMAIL_FROM_FORMAT = '{team_id}_{app_id}'
CONVERSATION_TYPE = 'slack'
SLACK_USER_ID_KEY = 'slack_user_id'


def get_action(resp, message_content, user_email, action_name, event):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data')
    candidate_profile = request_data.get('candidateProfileRequester', {}) if trigger_name == 'feedback_submitted' else request_data.get('candidateProfileReviewer', {})
    position = request_data.get('position', {})
    message_details = resp.get('message', {})
    app_id = message_details.get('bot_profile', {}).get('app_id')
    team_id = message_details.get('team') or resp.get('user', {}).get('team_id')
    return {
        'action_name': action_name,
        'request_data': {
            'conversationType': CONVERSATION_TYPE,
            'conversationId': trigger_name,
            'messageData': message_content,
            'emailTo': resp.get(SLACK_USER_ID_KEY) or resp.get('user', {}).get('id') or 'None',
            'emailFrom': EMAIL_FROM_FORMAT.format(team_id=team_id, app_id=app_id),
            'company': user_email,
            'profileId': candidate_profile.get('profileId'),
            'positionId': position.get('positionId'),
            'failureTime': 0 if resp.get('ok') else int(time.time()),
            'failureReason': resp.get('error'),
            'deliveryTime': int(float(message_details.get('ts') or 0))
        }
    }


def get_slack_user_by_email(email, bot_token):
    payload = {"email": email}
    headers = {'Authorization': 'Bearer ' + bot_token, 'Content-type': 'application/x-www-form-urlencoded'}
    resp = requests.get(url=SLACK_LOOKUP_BY_EMAIL_API_URL, params=payload, headers=headers)
    return resp.json()


def get_user_info_by_id(user_id, bot_token):
    payload = {"user": user_id}
    headers = {'Authorization': 'Bearer ' + bot_token, 'Content-type': 'application/x-www-form-urlencoded'}
    resp = requests.get(url=SLACK_USER_INFO_API_URL, params=payload, headers=headers)
    json_resp = resp.json()
    return json_resp


def _send_slack_message(bot_token, notif_text, slack_user_id, blocks):
    return requests.post(SLACK_CHAT_POST_MESSAGE_API_URL, {
            'token': bot_token,
            'text': notif_text if notif_text else None,
            'channel': slack_user_id,
            'blocks': json.dumps(blocks) if blocks else None
        }).json()


def send_slack_messages(user_email, bot_tokens, blocks, notif_text, event, data=None):
    actions = []
    message_content = {
        'slack_message_blocks': blocks,
        'data': data
    }
    for bot_token in bot_tokens:
        user_details = get_slack_user_by_email(user_email, bot_token)
        user_id = user_details.get('user', {}).get('id')
        if not user_id:
            print('user_id not found for email: {}'.format(user_email))
            actions.append(get_action(user_details, blocks, user_email, ADD_USER_MESSAGE_ACTION, event))
            continue

        json_resp = _send_slack_message(bot_token=bot_token, notif_text=notif_text, slack_user_id=user_id, blocks=blocks)

        if not json_resp.get('ok'):
            user_details['ok'] = False
            user_details['error'] = json_resp.get('error')
            actions.append(get_action(resp=user_details, message_content=message_content, user_email=user_email,
                                      action_name=ADD_USER_MESSAGE_ACTION, event=event))

        else:
            json_resp[SLACK_USER_ID_KEY] = user_id
            actions.append(get_action(resp=json_resp, message_content=message_content, user_email=user_email,
                                      action_name=ADD_USER_MESSAGE_ACTION, event=event))

    return actions


def send_feedback_message(event):
    trigger_name = event.get('trigger_name')
    request_data = event.get('request_data', {})

    notif_receiver = request_data.get('requester') if trigger_name == 'feedback_submitted' else request_data.get('reviewer')
    if not notif_receiver:
        raise ValueError('User to send notification to, not found in request data')

    notif_receiver_email = notif_receiver.get('redirectEmail') or notif_receiver.get('email')

    oauth_token = request_data.get('oauth_token')
    app_settings = event.get('app_settings', {})
    bot_token = app_settings.get('bot_token')
    bot_tokens = ([oauth_token] if oauth_token else None) or notif_receiver.get('slackTokens') or (
        [bot_token] if bot_token else None)

    if not bot_tokens:
        raise ValueError('bot_tokens not found for notification receiver')

    profile_feedback_id = request_data.get('feedbackId')
    data = {
        'profile_feedback_id': profile_feedback_id,
        'reminder_number': request_data.get('reminderCount', 0)
    }

    message_blocks, notif_text = message_builder.build_message(trigger_name, request_data)
    actions = send_slack_messages(user_email=notif_receiver_email, bot_tokens=bot_tokens, blocks=message_blocks,
                                  notif_text=notif_text, event=event, data=data)
    return actions

def send_approval_request(event):
    request_data = event.get('request_data', {})
    actions = None 
    for receiver in request_data.get('receivers', []):
        if not receiver.get('slack_tokens'):
            raise ValueError('bot_tokens not found for notification receiver')
        
        message_blocks = receiver.get('message_blocks')
        notif_text = receiver.get('notif_text')
        actions = send_slack_messages(user_email=receiver.get('email'), bot_tokens=receiver.get('slack_tokens'), blocks=message_blocks,
                                      notif_text=notif_text, event=event)
                                      

    return actions


def send_welcome_message(event):
    request_data = event.get('request_data', {})
    actions = []
    slack_user_id = request_data.get('messenger_app_data', {}).get('user_id')
    team_id = request_data.get('messenger_app_data', {}).get('team_id')
    app_id = request_data.get('messenger_app_data', {}).get('app_id')
    bot_token = request_data.get('messenger_app_data', {}).get('bot_token')
    if not bot_token or not slack_user_id:
        raise ValueError('bot_token or slack_user_id not found for welcome message slack_user_id: {}, app_id: {}, team_id: {}'.format(slack_user_id, app_id, team_id))

    blocks, notif_text = message_builder.build_message(WELCOME_MESSAGE_TRIGGER_NAME, request_data)
    json_resp = _send_slack_message(bot_token=bot_token, notif_text=notif_text, slack_user_id=slack_user_id, blocks=blocks)
    json_resp[SLACK_USER_ID_KEY] = slack_user_id

    user_info = get_user_info_by_id(slack_user_id, bot_token)
    user_email = user_info.get('user', {}).get('profile', {}).get('email')
    if not user_email:
        print('user_email not found for welcome message slack_user_id: {}, app_id: {}, team_id: {}'.format(slack_user_id, app_id, team_id))

    actions.append(get_action(resp=json_resp, message_content=blocks, user_email=user_email,
                              action_name=ADD_USER_MESSAGE_ACTION, event=event))

    return actions


def app_handler(event, context):
    try:
        trigger_name = event.get('trigger_name')

        if trigger_name == WELCOME_MESSAGE_TRIGGER_NAME:
            actions = send_welcome_message(event)

        elif trigger_name == T3S_APPROVAL_WORKFLOW_NOTIFICATION:
            actions = send_approval_request(event)

        else:
            actions = send_feedback_message(event)

        data = {'actions': actions}

    except Exception as ex:
        err_str = 'Handler failed with error: {}, traceback: {}, event: {}'.format(str(ex), traceback2.format_exc(), json.dumps(event))
        print(err_str)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback2.format_exc(),
            }),
        }
    
    print(data)
    return {
        'statusCode': 200,
        'body': json.dumps({'data': data})
    }
