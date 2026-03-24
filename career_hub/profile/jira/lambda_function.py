from bdb import set_trace
from email import header
import json
import os
import traceback

import arrow
import requests

from datetime import datetime
from datetime import timedelta

INSTANCE_URL = "https://api.atlassian.com/ex/jira/"
JIRA_LOGO_URL = 'https://static.vscdn.net/images/careers/demo/eightfolddemo-pborde-20201023/1650414281::jira-1.svg'
ACCESSIBLE_RESOURCES_URL = 'https://api.atlassian.com/oauth/token/accessible-resources'
NUM_RECORDS = 3

class JiraConnector():
    def __init__(self, oauth_token, domain_name):
        self.domain_name = domain_name
        print("domain name: ", self.domain_name)
        self.oauth_token = oauth_token
        self.headers = {
            'Authorization': 'Bearer ' + self.oauth_token
        }

    def get_cloud_id(self):
        response_data = requests.get(ACCESSIBLE_RESOURCES_URL, headers=self.headers)
        cloud_id = response_data.json()[0].get('id')
        print("cloud id: ", cloud_id)
        return cloud_id


    def get_url(self, username):
        since_last_30_days = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        cloud_id = self.get_cloud_id()
        url = INSTANCE_URL + '{}/rest/api/latest/search?'.format(cloud_id)
        return url

    def get_response(self, url, params):
        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_jira_user_name(self, app_settings, email):
        email_to_jira_user = app_settings.get('email_to_jira_user', {})
        user_name = email_to_jira_user.get(email)
        if user_name:
            print("user name: ", user_name)
            return user_name
        # if no user_name is provided then provided use email
        return email

    def get_demo_data(self, username):
        return {
            'title': 'Jira',
            'subtitle': username,
            'logo_url': JIRA_LOGO_URL,
                    'action_button': {
                        'label': 'View',
                        'onClick': 'https://www.atlassian.com/software/jira'
                    },
                    'table': {
                        'headers': ['Issues', 'Last modified at'],
                        'rows': [[{'value': 'Create an demo instance for demo user.'}, {'value': 'Apr 25, 2022'}],
                                [{'value': 'Update user instance for demo user.'}, {'value': 'Apr 24, 2022'}]]
                                }
                                }



def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        print("req data: ", req_data)
        oauth_token = req_data.get('oauth_token')
        app_settings = event.get('app_settings')
        email = req_data.get('email')
        domain_name = app_settings.get('domain_name')

        if not domain_name:
            domain_name = email.split('@')[1].split('.')[0]

        jc = JiraConnector(oauth_token, domain_name)
        username = jc.get_jira_user_name(app_settings, email)
        # set up demo app
        if app_settings.get('demo') == 'true':
            data = jc.get_demo_data(username)
            return {
                'statusCode': 200,
                'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
                }

        url = jc.get_url(username)
        jql=f"assignee='{username}' AND status=Open"
        params = {'jql': jql}

        try:
            resp_body = jc.get_response(url, params)    # response body JSON decoded as dict
        except Exception as e:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': repr(e),
                    'stacktrace': traceback.format_exc(),
                }),
            } 

        issues = resp_body.get('issues')
        rows = []
        for counter, issue in enumerate(issues):
            if counter > 2:
                break
            summary = issue.get('fields').get('summary')
            last_updated_at = arrow.get(issue.get('fields').get('updated'))
            print("issue: ", issue)
            issue_key = issue.get('key')
            row = [{'value' : summary, 'link': 'https://{}.atlassian.net/browse/{}'.format(jc.domain_name, issue_key)},
            {'value': last_updated_at.humanize() if last_updated_at else None}]
            rows.append(row)


        data = {
            'title': 'Jira',
            'logo_url': JIRA_LOGO_URL,
            'table': {
                    'headers': ['Issues', 'Last updated'],
                    'rows': rows
            }
        }

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
    result = app_handler(payload, None)
    print(80*'~')
    pprint(result)

if __name__ == '__main__':
    main()


