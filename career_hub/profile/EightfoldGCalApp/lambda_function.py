from __future__ import print_function
import json
import os
import requests
import os.path
import datetime

# If modifying these scopes, delete the file token.json.
INSTANCE_URL = 'https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=10&orderBy=startTime&singleEvents=True'
GOOGLE_LOGO_URL = 'https://images.fastcompany.net/image/upload/w_596,c_limit,q_auto:best,f_auto/fc/3050613-inline-i-2-googles-new-logo-copy.png'

class GCalConnector():
    def __init__(self, oauth_token):
        self.oauth_token = oauth_token
        self.headers = {
            'Authorization': 'Bearer ' + self.oauth_token
        }
    def get_response(self, url):
        resp = requests.get(url, headers=self.headers)
        return resp.json()


def app_handler(event, context):
   if event.get('trigger_name') == 'career_hub_home_sidebar_view':
        req_data = event.get('request_data', {})
        oauth_token = req_data.get('oauth_token')
        gcal = GCalConnector(oauth_token)
        # removed demo specific code (no demo)
        timeMin = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        events_url = INSTANCE_URL + '&timeMin={}'.format(timeMin)
        events = gcal.get_response(events_url)
        evs = []
        counter = 0
        for event in events.get('items', []):
            if counter > 2:
                break
            s = event['start'].get('dateTime')
            if not s:
                continue

            # get the date from datetime object
            start = s[0: 10]
            ev = [{'value': event.get('summary'), 'link': event.get('htmlLink')},{'value': start}]
            print(ev)
            evs.append(ev)
            counter += 1

        data = {
            'title': 'Google Calendar',
            'logo_url': GOOGLE_LOGO_URL,
            'table': {
                    'headers': ['Event', 'Time'],
                    'rows': evs
            }
        }
        print(data)

        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
            }

def main():
    import pprint
    from pprint import pprint
    payload = {}

    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
       payload = json.load(f)

    print(payload)
    result = app_handler(payload, None)
    print(80*'~')
    pprint(result)

if __name__ == '__main__':
    main()
