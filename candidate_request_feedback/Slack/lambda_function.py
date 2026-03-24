import json
from datetime import datetime
from collections import OrderedDict
import requests
import os
import logging
import time
import traceback
import timeago
import jinja2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SLACK_USER_ID_FROM_EMAIL_URL = "https://slack.com/api/users.lookupByEmail"
SLACK_CHAT_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'

SLACK_LOGO_URL = 'https://www.kansasfest.org/wp-content/uploads/slack.png'

def _get_slack_user(token, email):
    resp = requests.get(
        url=SLACK_USER_ID_FROM_EMAIL_URL,
        params={
        'token': token,
        'email': email,
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('user', {})

    return None

def _post_slack_message(bot_token, channel, text, blocks):
    resp = requests.get(
        url=SLACK_CHAT_POST_MESSAGE_URL,
        params={
            'text': text,
            'blocks': blocks,
            'channel': channel,
            'token': bot_token,
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))
    print(json_resp)
    if json_resp.get('ok'):
        return json_resp

    return None

def app_handler(event, context):
    if event.get('trigger_name') == 'candidate_feedback_request':
      app_settings = event.get('app_settings', {})
      BOT_TOKEN = app_settings.get('bot_token')
      email_swap_map = app_settings.get('email_swap_map', {})

      req_data = event.get('request_data', {})
      sender_email = req_data.get('sender_email')
      recipient_email  = req_data.get('recipient_email')
      recipient_email = email_swap_map.get(recipient_email) or recipient_email
      ef_profiles = req_data.get('profiles')
      ef_position = req_data.get('position')
      feedback_url = req_data.get('feedback_url')

      # if BOT_TOKEN or not current_user_email or not ef_profiles:
      #     return {
      #         'statusCode': 400,
      #         'body': 'Please provide email and token in app_settings'
      #     }

      try:
          sender_slack_user = _get_slack_user(BOT_TOKEN, sender_email)
          if not sender_slack_user:
              raise Exception('Sorry, we were unable to retrieve a Slack profile for this user. {}'.format(sender_email))
          sender_slack_user_id = sender_slack_user.get('id')
          sender_slack_user_profile = sender_slack_user.get('profile', {})

          recipient_slack_user = _get_slack_user(BOT_TOKEN, recipient_email)
          if not recipient_slack_user:
              raise Exception('Sorry, we were unable to retrieve a Slack profile for this user. {}'.format(recipient_email))
          recipient_slack_user_id = recipient_slack_user.get('id')
          recipient_slack_user_profile = recipient_slack_user.get('profile', {})


          PROFILE_BLOCK_TEMPLATE = """
              {
                 "type":"divider"
              },
              {
                 "type":"section",
                 "accessory":{
                    "type":"image",
                    "image_url":"{{image_url}}",
                    "alt_text":"{{fullname}}"
                 },
                 "text":{
                    "type":"mrkdwn",
                    "text":"*<{{profile_url}}|{{fullname}}>*\n{{title}}\n{{location}}"
                 }
              },
          """

          profile_blocks = ''.join([
              jinja2.Template(PROFILE_BLOCK_TEMPLATE).render(
                  title=pr.get('title'),
                  profile_url=feedback_url,
                  location=pr.get('location'),
                  fullname=pr.get('fullname'),
                  image_url=pr.get('image_url'),
              ).strip()
              for pr in ef_profiles[:2]]).strip()

          OVERFLOW_PROFILES_BLOCK_TEMPLATE = """
              {
                  "type": "context",
                  "elements": [
                      {{overflow_profile_elements}},
                      {
                          "type": "mrkdwn",
                          "text": "*<{{feedback_url}}|+{{count_overflow_profiles}} more>*"
                      }
                  ]
              },
              {
                  "type": "divider"
              }, 
          """


          OVERFLOW_PROFILE_ELEMENT_TEMPLATE = """
              {
                  "type": "image",
                  "alt_text": "{{fullname}}",
                  "image_url": "{{image_url}}"
              }
          """

          overflow_profiles_block = ''
          if len(ef_profiles) > 2:
              overflow_profile_elements = ','.join([
              jinja2.Template(OVERFLOW_PROFILE_ELEMENT_TEMPLATE).render(
                      fullname=pr.get('fullname'),
                      image_url=pr.get('image_url'),
                  ).strip()
              for pr in ef_profiles[2:]]).strip()

              overflow_profiles_block = jinja2.Template(OVERFLOW_PROFILES_BLOCK_TEMPLATE).render(
                  feedback_url=feedback_url,
                  count_overflow_profiles=len(ef_profiles) - 2,
                  overflow_profile_elements=overflow_profile_elements,
              ).strip()

          POSITION_LINK_TEMPLATE = " for:\n*<{{position_url}}|{{position_name}}>*"
          position_link = ''
          if ef_position:
              position_link = jinja2.Template(POSITION_LINK_TEMPLATE).render(
                  position_name=ef_position.get('title'),
                  position_url=ef_position.get('pipeline_url'),
              )

          SLACK_MESSAGE_TEMPLATE = """
              [
                 {
                    "type":"section",
                    "text":{
                       "type":"mrkdwn",
                       "text":"Hi {{recipient_name}}! :wave:"
                    }
                 },
                 {
                    "type":"section",
                    "text":{
                       "type":"mrkdwn",
                       "text":"{{sender_name}} wants your feedback on the following candidates{{position_link}}"
                    }
                 },
                 {{profile_blocks}}
                 {
                    "type":"divider"
                 },
                 {{overflow_profiles_block}}
                 {
                    "type":"actions",
                    "elements":[
                       {
                          "type":"button",
                          "text":{
                             "type":"plain_text",
                             "emoji":true,
                             "text":"Provide Feedback"
                          },
                          "style":"primary",
                          "value":"click_me_123",
                          "url":"{{feedback_url}}"
                       }
                    ]
                 }
              ]
          """   

          blocks = jinja2.Template(SLACK_MESSAGE_TEMPLATE).render(
              feedback_url=feedback_url,
              profile_blocks=profile_blocks,
              position_link=position_link or ':',
              overflow_profiles_block=overflow_profiles_block,
              sender_name=sender_slack_user_profile.get('real_name'),
              recipient_name=recipient_slack_user_profile.get('real_name'),
          )

          ret = _post_slack_message(
              bot_token=BOT_TOKEN, 
              channel='@{}'.format(recipient_slack_user_id), 
              text='You have a new feedback request', 
              blocks=blocks,
          )

      except Exception as ex:
          print(traceback.format_exc())

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
      
