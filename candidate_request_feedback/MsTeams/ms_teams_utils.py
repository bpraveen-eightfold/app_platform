from __future__ import absolute_import

import requests
import glog as log

AUTHORITY = 'https://login.microsoftonline.com'

TOKEN_URL = '{0}{1}'.format(AUTHORITY, '/common/oauth2/v2.0/token')
BOT_TOKEN_URL = '{0}{1}'.format(AUTHORITY, '/botframework.com/oauth2/v2.0/token')

def send_message_from_bot(token_data, recipient_teams_data, message=None, adaptive_card=None):
    payload = {
        'type': 'message',
        'from': token_data.get('bot'),
        'recipient': recipient_teams_data.get('recipient') # this API though not mentioned in the doc works without conversation
    }
    if adaptive_card:
        payload.update({
            'attachments': [{
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': adaptive_card
            }]
        })
    else:
        payload.update({'text': message})
    response = requests.post(
        '{}/v3/conversations/{}/activities/{}'.format(recipient_teams_data.get('serviceUrl'),
            recipient_teams_data.get('conversation').get('id'), recipient_teams_data.get('activityId')),
        json=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(token_data.get('bot_token').get('access_token'))
        }
    )

    if not response.status_code in [200, 201]:
        log.error('Error: {0}: {1}'.format(
            response.status_code, response.text))

    return response.json()
