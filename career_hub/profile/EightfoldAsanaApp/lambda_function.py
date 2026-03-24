import json
import time
import pytz
import six
from datetime import datetime
from datetime import timedelta
import requests
import timeago
import traceback


INSTANCE_URL = "https://app.asana.com/api/1.0/"
ASANA_LOGO_URL = 'https://static.vscdn.net/images/career_hub/profile/asana.png'
NUM_RECORDS = 3

def to_timestamp(dt, default=0):
    if not dt:
        return default
    try:
        if isinstance(dt, (str, six.text_type)):
            dt = du.parse(dt)
        # if date has a timezone not the same as utc, then convert to utc
        if isinstance(dt, datetime) and dt.utcoffset() and dt.utcoffset().seconds:
            utc = pytz.timezone('UTC')
            dt = utc.normalize(dt.astimezone(utc))
        # NOTE: timetuple() does not include microsecond part of dt, so add it explicitly
        t = (time.mktime(dt.timetuple()) + dt.microsecond/1000000.) if dt else default
        return t
    except:
        print('Failed to convert to_timestamp {}'.format(dt))
        return default

class AsanaConnector():
    def __init__(self, cfg):
        self.max_tasks = cfg.get('max_tasks', NUM_RECORDS)
        self.api_key = cfg.get('api_key')
        self.headers =  {
            'Authorization': 'Bearer ' + self.api_key
        }

    def _get_response(self, url):
        resp = requests.get(url, headers=self.headers, timeout=60)
        return resp.json()

    def get_user_workspace_tasks(self, user_gid, workspace_id, limit=100):
        since_last_90_days = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        query = 'tasks?assignee={user_gid}&workspace={workspace_id}&limit={limit}&modified_since={since}&opt_fields=name,gid,completed,modified_at'.format(
                user_gid=user_gid, workspace_id=workspace_id, limit=limit, since=since_last_90_days)
        url = INSTANCE_URL + query
        resp = self._get_response(url)
        completed_tasks = 0
        tasks_data = []
        while resp.get('next_page'):
            completed_tasks += sum([1 for record in resp.get('data') if record.get('completed')])
            for record in resp.get('data'):
                modified_at = datetime.strptime(record.get('modified_at'), '%Y-%m-%dT%H:%M:%S.%fZ') if record.get('modified_at') else None
                modified_at = int(to_timestamp(modified_at)) if modified_at else 0
                tasks_data.append({'name': record.get('name'),
                                   'gid': record.get('gid'),
                                   'modified_at': modified_at})
            query = 'tasks?assignee={user_gid}&workspace={workspace_id}&limit={limit}&offset={offset}&modified_since={since}&opt_fields=name,gid,completed,modified_at'.format(
                    user_gid=user_gid, workspace_id=workspace_id, limit=limit, offset=resp.get('next_page')['offset'], since=since_last_90_days)
            url = INSTANCE_URL + query
            resp = self._get_response(url)
        completed_tasks += sum([1 for record in resp.get('data') if record.get('completed')])
        for record in resp.get('data'):
            modified_at = datetime.strptime(record.get('modified_at'), '%Y-%m-%dT%H:%M:%S.%fZ') if record.get('modified_at') else None
            modified_at = int(to_timestamp(modified_at)) if modified_at else 0
            tasks_data.append({'name': record.get('name'),
                               'gid': record.get('gid'),
                               'modified_at': modified_at})
        tasks_data = sorted(tasks_data, key=lambda i: i['modified_at'], reverse=True)
        return completed_tasks, tasks_data[0:self.max_tasks]

    def get_user_tasks(self, user_gid, workspace_ids):
        completed_tasks = 0
        tasks_data = []
        for wid in workspace_ids:
            n_tasks, t_data = self.get_user_workspace_tasks(user_gid, wid)
            completed_tasks += n_tasks
            tasks_data.extend(t_data)
        # remove the dup tasks
        gid_to_tasks = {}
        for t_data in tasks_data:
            gid_to_tasks[t_data['gid']] = t_data
        tasks_data = gid_to_tasks.values()
        tasks_data = sorted(tasks_data, key=lambda i:i['modified_at'], reverse=True)
        return completed_tasks, tasks_data[0:self.max_tasks]

    def _get_user_tasks_list(self, user_gid, workspace_id):
        query = 'users/{user_gid}/user_task_list?workspace={workspace_id}'.format(
                user_gid=user_gid, workspace_id=workspace_id)
        url = INSTANCE_URL + query
        resp = self._get_response(url)

    def _get_task_detail(user_gid, task_gid):
        query = 'tasks/{task_gid}'.format(task_gid=task_gid, workspace_id=workspace_id)
        url = INSTANCE_URL + query
        resp = self._get_response(url)

    def _get_recent_tasks(self, user_gid, workspace_id):
        query = 'workspaces/{workspace_gid}/tasks/search?created_by.any={user_gid}&icommented_on_by.any={user_gid}&opt_fields=modified_at,name'.format(
                user_gid=user_gid, workspace_gid=workspace_id)
        url = INSTANCE_URL + query
        resp = self._get_response(url)
        ret = []
        for record in resp.get('data'):
            #task_details = self._get_task_detail(user_gid, record.get('gid'))
            ret.append({'name': record.get('name'),
                        'gid': record.get('gid'),
                        'modified_at': record.get('modified_at')})
            if len(ret) >= self.max_tasks:
                break
        return ret

    def get_user_details(self, email):
        query = "users/{user_gid}".format(user_gid=email)
        url = INSTANCE_URL + query
        resp = self._get_response(url)
        user_gid = resp.get('data').get('gid')
        workspace_ids = []
        for record in resp.get('data').get('workspaces'):
            workspace_ids.append(record.get('gid'))
        return {'user_gid': user_gid,
                'workspace_ids': workspace_ids,
                'name': resp.get('data').get('name')}

    def get_num_projects_in_workspace(self, user_id, workspace_id):
        print('fetching asana projects for user_id: {}'.format(user_id))
        query = "projects?workspace={workspace_id}&archived={archived}&opt_fields=name,members,owner,current_status".format(
                workspace_id=workspace_id, archived=False)
        url = INSTANCE_URL + query
        resp = self._get_response(url)
        ret = []
        for record in resp.get("data", []):
            for member in record.get("members"):
                if member.get("gid") == user_id:
                    ret.append(record)
        return len(ret)

    def get_num_projects(self, user_gid, workspace_ids):
        num_projects = 0
        for wid in workspace_ids:
            num_projects += self.get_num_projects_in_workspace(user_gid, wid)
        return num_projects

    def _get_asana_project_details(self, project_id):
        print('fetching asana project details for project: {}'.format(project_id))
        query = "projects/" + project_id
        url = INSTANCE_URL + query
        response = requests.get(url, headers=self.headers, timeout=60)
        ret = {}
        try:
            ret = response.json().get("data", {})
        except Exception as ex:
            print(str(ex))
            return ret
        return ret


def app_handler(event, context):
    if event.get('trigger_name') == 'career_hub_profile_view':
        req_data = event.get('request_data', {})
        app_settings = event.get('app_settings')
        email = req_data.get('employee_email') or req_data.get('email')
        if not email or not app_settings or not app_settings.get('api_key'):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Please provide email and api_key in app_settings'}),
            }

        email_swap_map = app_settings.get('email_swap_map', {})
        email = email_swap_map.get(email) or email
        ac = AsanaConnector(app_settings)
        try:
            print('Fetching data for email: {}'.format(email))
            data = {'title': 'Asana',
                    'logo_url': ASANA_LOGO_URL}

            user_details = ac.get_user_details(email)
            user_gid = user_details.get('user_gid')
            print('user_gid: {} for email: {}'.format(user_gid, email))
            if not user_gid:
                data['error'] = 'Asana account not found for email {}'.format(email)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
                }
            completed_tasks, recent_tasks = ac.get_user_tasks(user_gid, user_details.get('workspace_ids'))
            print('recent_tasks: {} for email: {}'.format(recent_tasks, email))
            #num_projects = ac.get_num_projects(user_gid, user_details.get('workspace_ids'))
            now  = datetime.now()
            count = 0
            rows = []
            for task in recent_tasks:
                modified_at = datetime.fromtimestamp(task.get('modified_at'))
                rows.append([{'value': task.get('name'),
                              'link': 'https://app.asana.com/0/0/{task_gid}'.format(task_gid=task.get('gid'))},
                             {'value': timeago.format(modified_at, now) if modified_at else None}])
                count += 1
                if count >= ac.max_tasks:
                    break

            data = {
                'title': 'Asana',
                'subtitle': '@{}'.format(user_details['name']),
                'logo_url': ASANA_LOGO_URL,
                'tiles': [
                    {'header': 'Completed Tasks over last 90 days', 'value': completed_tasks},
                ],
                'table': {
                    'headers': ['Recent Tasks', 'Last Activity'],
                    'rows': rows
                }
            }

        except Exception as ex:
            print(traceback.format_exc())

            error = 'Asana account not found for email {}'.format(email)

            data = {
                'error': error,
                'title': 'Asana',
                'logo_url': ASANA_LOGO_URL,
                'stacktrace': traceback.format_exc() or 'Internal Error',
            }

            return {
                'statusCode': 200,
                'body': json.dumps({'data': data })
            }
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
        }
