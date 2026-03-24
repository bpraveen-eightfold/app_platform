from __future__ import absolute_import

import json
import traceback
import glog

import ms_teams_utils
from teams_message_handler_registry import teams_message_handler_registry
from teams_notification_types import TeamsNotificationTypes

def app_handler(event, context):
    try:
        # This code temporarily contains lot of hardcoded info
        request_data = event.get('request_data', {})
        app_settings = event.get('app_settings', {})
        trigger_name = event.get('trigger_name')
        glog.info('request_data: {},trigger_name: {}'.format(request_data, trigger_name))
        adaptive_card_str = teams_message_handler_registry.get(trigger_name)(request_data, app_settings, trigger_name).get_message_content()
        adaptive_card = json.loads(adaptive_card_str)
        token_dict = get_ms_token_data(trigger_name, request_data, app_settings)
        ms_teams_utils.send_message_from_bot(token_dict.get('token_data'), token_dict.get('recipient_teams_data'), adaptive_card=adaptive_card)
    except Exception as ex:
        glog.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'data': {'success': True}})
    }

def get_ms_token_data(trigger_name, request_data, app_settings):
    token_trigger_mapping = {
        TeamsNotificationTypes.FEEDBACK_REQUESTED._value_: 'reviewer',
        TeamsNotificationTypes.FEEDBACK_SUBMITTED._value_: 'requester',
        TeamsNotificationTypes.FEEDBACK_REMINDER._value_: 'reviewer',
        TeamsNotificationTypes.FEEDBACK_CANCELLED._value_: 'reviewer'
    }
    token_data = request_data.get(token_trigger_mapping.get(trigger_name)).get('msToken')
    return {
        'token_data': {
            'bot': token_data.get('bot'),
            'bot_token': token_data.get('bot_token')
        },
        'recipient_teams_data': {
            'serviceUrl': token_data.get('serviceUrl'),
            'conversation': token_data.get('conversation'),
            'activityId': token_data.get('activityId'),
            'recipient': token_data.get('user')
        }
    }
