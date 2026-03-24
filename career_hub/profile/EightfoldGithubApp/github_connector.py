from datetime import datetime
from datetime import timedelta

import requests
from requests.auth import HTTPBasicAuth

from constants import API_URL


class GithubConnector():
    def __init__(self, cfg):
        self.cfg = cfg
        self.username = cfg.get('username')
        self.token = cfg.get('token')
        self.auth = HTTPBasicAuth(self.username, self.token)
        self.headers = {'Accept': 'application/vnd.github.v3+json'}
        self.now = datetime.now()
        self.one_month_ago = self.now - timedelta(days=30)

    def _get_resp(self, url):
        resp = requests.get(url, auth = self.auth, headers=self.headers, timeout=60)
        return resp.json()

    def get_prs(self, user_name, qualifier, activity_type, limit=100):
        pr_list = []
        page = 1
        query = f'search/issues?q={qualifier}:{user_name}&per_page={limit}&page={page}'
        resp = self._get_resp(API_URL + query)
        items = resp.get('items', [])
        count = len(items)
        total_count = resp.get('total_count', count)
        fetch_more_page = True
        num_prs = 0
        timestamp_field = 'created_at' if activity_type == 'Created' else 'updated_at'
        for item in items:
            pr_list.append({
                'title': item.get('title', ''),
                'link': item.get('pull_request', {}).get('html_url', ''),
                'activity_type': activity_type,
                'timestamp': datetime.strptime(item.get(timestamp_field), '%Y-%m-%dT%H:%M:%SZ') if item.get(timestamp_field) else None
            })
            if len(pr_list) >= 3:
                break
        for item in items:
            timestamp = datetime.strptime(item.get(timestamp_field), '%Y-%m-%dT%H:%M:%SZ') if item.get(timestamp_field) else None
            if timestamp >= self.one_month_ago:
                num_prs += 1
            else:
                fetch_more_page = False
                break
        page += 1
        while fetch_more_page and count < total_count:
            query = f'search/issues?q={qualifier}:{user_name}&per_page={limit}&page={page}'
            resp = self._get_resp(API_URL + query)
            count += len(resp['items'])
            page += 1
            for item in resp['items']:
                created_at = datetime.strptime(item.get('created_at'), '%Y-%m-%dT%H:%M:%SZ') if item.get('created_at') else None
                if created_at >= self.one_month_ago:
                    num_prs += 1
                else:
                    fetch_more_page = False
                    break
        return num_prs, pr_list
