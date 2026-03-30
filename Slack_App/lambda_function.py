import json
from datetime import datetime
from collections import OrderedDict
import requests
import os
import logging
import time
import traceback
import timeago

logger = logging.getLogger()
logger.setLevel(logging.INFO)

INSTANCE_URL = "https://app.asana.com/api/1.0/"
SLACK_USER_ID_FROM_EMAIL_URL = "https://slack.com/api/users.lookupByEmail"
SLACK_USER_CONVERSATIONS_URL = "https://slack.com/api/users.conversations"
SLACK_CONVERSATIONS_INFO_URL = "https://slack.com/api/conversations.info"
SLACK_CONVERSATIONS_HISTORY_URL = "https://slack.com/api/conversations.history"
SLACK_REACTIONS_LIST_URL = 'https://slack.com/api/reactions.list'
SLACK_SEARCH_MESSAGES_URL = 'https://slack.com/api/search.messages'

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

def _get_slack_channels_for_user(token, user_id, exclude_archived=True, limit=200):
    resp = requests.get(
        url=SLACK_USER_CONVERSATIONS_URL,
        params={
            'token': token,
            'user': user_id,
            'exclude_archived': exclude_archived,
            'limit': limit,
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('channels', [])

    return None

def _get_slack_channels_history(token, channel_id, limit=200):
    resp = requests.get(
        url=SLACK_CONVERSATIONS_HISTORY_URL,
        params={
            'token': token,
            'channel': channel_id,
            'limit': limit,
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('messages', [])

    return None

def _get_slack_user_reactions(token, user_id=None, limit=50):
    resp = requests.get(
        url=SLACK_REACTIONS_LIST_URL,
        params={
            'token': token,
            'user': user_id,
            'limit': limit,
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('items', [])

    return None


def _get_slack_channel_info(token, channel_id):
    resp = requests.get(
        url=SLACK_CONVERSATIONS_INFO_URL,
        params={
            'token': token,
            'channel': channel_id,
            'include_num_members': True
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('channel', [])

    return None


def _get_slack_search_results_for_user(token, user_id, count=100, page=1):
    resp = requests.get(
        url=SLACK_SEARCH_MESSAGES_URL,
        params={
            'page': page,
            'count': count,
            'token': token,
            'sort_dir': 'desc',
            'sort': 'timestamp',
            'query': 'from:<@{}>'.format(user_id),
        },
    )

    json_resp = json.loads(json.dumps(resp.json()))

    if json_resp.get('ok'):
        return json_resp.get('messages', {}).get('matches')

    return None



def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings', {})

        email = req_data.get('employee_email') or req_data.get('email')
        current_user_email = req_data.get('current_user_email')

        if not email or not app_settings or not app_settings.get('token'):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Please provide email and token in app_settings'}),
            }

        try:
            TOKEN = app_settings.get('token')
            ignore_channels = app_settings.get('ignore_channels', [])
            email_swap_map = app_settings.get('email_swap_map', {})

            email = email_swap_map.get(email) or email
            current_user_email = email_swap_map.get(current_user_email) or current_user_email
            print('Fetching Slack data for email: {}'.format(email))

            target_slack_user = _get_slack_user(TOKEN, email)
            if not target_slack_user:
                raise Exception('Sorry, we were unable to retrieve a Slack profile for this user.')

            print('Slack user_id is: {}'.format(target_slack_user.get('id')))
            target_slack_user_profile = target_slack_user.get('profile', {})
            target_profile_display_name = target_slack_user_profile.get('display_name')
            target_profile_real_name = target_slack_user_profile.get('real_name')


            slack_user_channels = _get_slack_channels_for_user(TOKEN, target_slack_user.get('id'))
            target_slack_channels_count = '200+' if len(slack_user_channels) > 200 else str(len(slack_user_channels))
            slack_user_channels = {c.get('id'): c for c in slack_user_channels}


            mutual_channels = None
            # if email != current_user_email:
            #     current_slack_user = _get_slack_user(TOKEN, current_user_email)
            #     if current_slack_user:
            #         slack_user_channel_ids = set(slack_user_channels.keys())
            #         current_user_slack_channel_ids = set([c.get('id') for c in _get_slack_channels_for_user(TOKEN, current_slack_user.get('id'))])

            #         set_diff = slack_user_channel_ids.difference(current_user_slack_channel_ids)

            #         mutual_channels = len(set_diff)
            #         if len(slack_user_channel_ids) >= 200 or len(current_user_slack_channel_ids) >= 200:
            #             mutual_channels += '+' 

            target_user_search_results = []
            for page in range(1, 3):
                target_user_search_results.extend(_get_slack_search_results_for_user(TOKEN, target_slack_user.get('id'), page=page))

            target_user_search_results = [
                sr for sr in target_user_search_results 
                if sr.get('type') == 'message' 
                    and not sr.get('channel', {}).get('is_private')
                    and not sr.get('channel', {}).get('is_general')
                    and sr.get('channel', {}).get('name') not in ignore_channels
            ]


            target_user_most_recent_channels = OrderedDict()
            for sr in target_user_search_results:
                channel_id = sr.get('channel', {}).get('id')
                if sr.get('channel', {}).get('id') not in target_user_most_recent_channels:
                    target_user_most_recent_channels[channel_id] = sr.get('ts', {})


            # target_user_reactions = _get_slack_user_reactions(TOKEN, target_slack_user.get('id'), 200)
            # target_user_reactions = [r for r in target_user_reactions if r.get('type') == 'message']

            # target_user_most_recent_channels = OrderedDict()
            # for r in target_user_reactions:
            #     if r.get('channel') not in target_user_most_recent_channels:
            #         target_user_most_recent_channels[r.get('channel')] = r

            channel_info = []
            for channel_id, timestamp in target_user_most_recent_channels.items():
                channel = slack_user_channels.get(channel_id)
                if channel:
                    channel_info.append({'channel': channel, 'timestamp': float(timestamp)})

            # target_user_most_recent_messages = {}
            # for channel in channel_info:
            #     channel_id = channel.get('id')
            #     channel_messages = _get_slack_channels_history(TOKEN, channel_id, 100)

            #     for message in channel_messages:
            #         if message.get('user') == target_slack_user.get('id'):
            #             target_user_most_recent_messages[channel_id] = message.get('ts', 0)
            #             break

            rows = []
            for c_info in channel_info:
                channel = c_info.get('channel')
                timestamp = c_info.get('timestamp')
                channel_id = channel.get('id')

                latest_time = timestamp

                row = ([
                    {'value': '#{}'.format(channel.get('name')), 'link': 'https://slack.com/app_redirect?channel={}'.format(channel_id)},
                    {'value': timeago.format(latest_time, datetime.now())},
                ], latest_time)

                rows.append(row)


            rows.sort(key=lambda x: x[1], reverse=True)
            rows = [r[0] for r in rows][:5]

            tiles = [{'header': 'Channels', 'value': target_slack_channels_count}]
            if mutual_channels:
                tiles.append({'header': 'Mutual Channels', 'value': mutual_channels})

            data = {
                'title': 'Slack',
                'logo_url': SLACK_LOGO_URL,
                'subtitle': '@{}'.format(target_profile_display_name) if target_profile_display_name else target_profile_real_name,
                'action_button': {
                    'label': 'Message',
                    'onClick': 'window.open("https://slack.com/app_redirect?channel={}");'.format(target_slack_user.get('id')),
                },
                'tiles': tiles,
                'table': {
                    'headers': ['Recently Active Public Channels', 'Last Activity'],
                    'rows': rows,
                } if rows else None,
                'footer': 'No recent activity in public channels.' if not rows else None,
            }

        except Exception as e:
            print(traceback.format_exc())

            error = 'Sorry, we are currently unable to connect to Slack.'
            if str(e) in [
                'Sorry, we were unable to retrieve a Slack profile for this user.',
            ]:
                error = str(e)

            data = {
                'error': error,
                'title': 'Slack',
                'logo_url': SLACK_LOGO_URL,
                'stacktrace': traceback.format_exc() or 'Internal Error',
            }

            return {
                'statusCode': 200,
                'body': json.dumps({'data': data })
            }

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800}, indent=4, sort_keys=True)
        }
