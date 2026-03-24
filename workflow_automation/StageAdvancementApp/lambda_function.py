from __future__ import absolute_import

import json
import traceback

from stage_advancement import StageAdvancement


def _build_action_request_data(request_data, template_dict):
    return {
        'fromName': template_dict.get('from_name'),
        'emailTo': template_dict.get('email_to'),
        'replyTo': template_dict.get('reply_to'),
        'extraVarsToSubstitute': template_dict.get('extra_vars_to_substitute'),
        'templateId': template_dict.get('template_id'),
        'templateName': template_dict.get('template_name'),
        'templateCategory': template_dict.get('template_category'),
        'subject': template_dict.get('email_subject'),
        'body': template_dict.get('email_body'),
        'emailFrom': template_dict.get('email_from'),
        'emailBcc': template_dict.get('email_bcc'),
        'userCalendarEventId': None,
        'plannedEventId': None,
        'profileFeedbackId': None,
        'campaignId': None,
        'positionId': request_data.get('position', {}).get('positionId'),
        'profileId': request_data.get('candidateProfile', {}).get('profileId')
    }


def build_action(request_data, template_dict):
    template_to_action_map = {
        'email_template': 'send_email_with_template_v2',
        'scheduling_template': 'schedule_interview_action',
        'whatsapp_template': 'send_whatsapp_notification'
    }
    template_type = template_dict.get('template_type')
    action_name = template_to_action_map.get(template_type)
    if not action_name:
        print('Action not mapped for template_type: {}'.format(template_type))
        return {}

    action_request_data = _build_action_request_data(request_data, template_dict)

    return {
        'action_name': action_name,
        'request_data': action_request_data
    }


def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    request_data = event.get('request_data', {})
    print({'request_data': request_data})
    try:
        stage_advancement = StageAdvancement(request_data)
        rules = app_settings.get('rules', [])
        actions = []
        for rule_dict in rules:
            if not stage_advancement.evaluate_rule(rule_dict):
                continue
            notification_templates = rule_dict.get('notification_templates', [])
            for template_dict in notification_templates:
                template_dict = stage_advancement.substitute_values_in_dict(template_dict)
                action = build_action(request_data, template_dict)
                if action:
                    actions.append(action)

        data = {'actions': actions}
        response = {
            'statusCode': 200,
            'body': {'data': data}
        }
        print({'app_response': response})
        return response
    except Exception as ex:
        trigger_name = event.get('trigger_name', '')
        err_str = 'Handler for trigger_name: {} failed with error: {}, traceback: {}'.format(
            trigger_name, str(ex), traceback.format_exc())
        print(err_str)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': repr(ex),
                'stacktrace': traceback.format_exc(),
            }),
        }
