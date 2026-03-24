#!/usr/bin/env python
import sys
import glog as log
import json
import traceback
import requests
import os
import shutil
import tempfile
import zipfile
import datetime
import paramiko
import csv
import time
from enum import Enum

AUTHORIZATION_TOKEN = 'Basic MU92YTg4T1JyMlFBVktEZG8wc1dycTdEOnBOY1NoMno1RlFBMTZ6V2QwN3cyeUFvc3QwTU05MmZmaXFFRDM4ZzJ4SFVyMGRDaw=='
ACCESS_TOKEN_URL = 'https://apiv2.eightfold.ai/oauth/v1/authenticate'

FREQUENCY = {
    'WEEKLY': 7,
    'DAILY': 1,
    'HOURLY': 24
}


def _errordict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'error': kwargs['message'],
            'stacktrace': traceback.format_exc()
        })
    }


class ConfiguredFrequecy(Enum):
    HOURLY = 'HOURLY'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


class SupportedExporters(Enum):
    SFTP = 'sftp'
    EMAIL = 'email'
    FILE = 'file'


def _successdict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'message': kwargs['message']
        })
    }


class ApiConnector:
    def __init__(self, oauth_username, oauth_password):
        self.oauth_username = oauth_username
        self.oauth_password = oauth_password

        self.data = {
            "grantType": "password",
            "username": self.oauth_username,
            "password": self.oauth_password
        }

        self.headers = {
            'Authorization': AUTHORIZATION_TOKEN
        }

        self.access_token = requests.post(ACCESS_TOKEN_URL, json=self.data, headers=self.headers).json().get(
            'data').get('access_token')
        log.info("Access Token: {}".format(self.access_token))
        self.profile_ids = []
        self.mapping_file_name = ''
        self.base_name = ''
        self.result_filename_prefix = ''

    def get_message_ids(self, start_ts, end_ts):
        base_url = f"http://apiv2.eightfold.ai/api/v2/core/changelog/user-messages?startTime={start_ts}&endTime={end_ts}&start="
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'accept': 'application/json'
        }

        url = base_url + "0"
        log.info("First URL: {}".format(url))

        response = requests.get(url, headers=headers).json()
        meta_data = response.get('meta')
        log.info("Meta Data: {}".format(response.get('meta')))

        data = response.get('data')
        entity_ids = [entity['entityId'] for entity in data]

        total_pages = (meta_data.get('totalCount') // 1000) + 1
        for i in range(1, total_pages):
            url = base_url + str(i)
            log.info("Current URL: {}".format(url))
            response = requests.get(url, headers=headers)

            if response and response.status_code == 200:
                meta_data = response.json().get('meta')
                log.info("Meta Data: {}".format(meta_data))

                data = response.json().get('data')
                entity_ids = entity_ids + [entity['entityId'] for entity in data]
            else:
                log.info(f'API execution failed with error msg: {response.text}')

        return entity_ids

    def write_to_file(self, email_content, output_file_name):
        local_path = os.path.join(self.base_name, output_file_name)
        # log.info('Writing to local file: {}'.format(local_path))
        with open(local_path, 'w') as temp_writer:
            temp_writer.write(email_content)
        return local_path

    def zipper(self, host, username, sftp_path, private_key):
        zipped_file = shutil.make_archive(self.base_name, 'gztar', self.base_name)
        log.info(f'zipped file is created with name: {zipped_file}')
        self.transport(zipped_file, host, username, sftp_path, private_key)
        os.remove(zipped_file)
        log.info(f'Zip file: {zipped_file} is removed.')

    def transport(self, zipper_file, host, username, sftp_path, private_key):
        id_path = tempfile.mkdtemp()
        id_key_path = os.path.join(id_path, 'id_rsa')
        with open(id_key_path, 'w', encoding='utf_8') as f:
            f.write(private_key)
        os.chmod(id_key_path, 0o600)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            host,
            username=username,
            key_filename=id_key_path,
            look_for_keys=False,
            allow_agent=False,
        )
        sftp = ssh.open_sftp()
        try:
            self._sftp_makedirs(sftp, sftp_path)
            sftp.chdir(sftp_path)
            remote_filename = os.path.basename(zipper_file)
            sftp.put(zipper_file, remote_filename)
            log.info(f"SFTP upload complete: {remote_filename} -> {sftp_path}")
        finally:
            sftp.close()
            ssh.close()

    @staticmethod
    def _sftp_makedirs(sftp, remotedir, mode=0o777):
        """Recursively ensure remote directories exist via chdir probing."""
        if remotedir == '/':
            return
        try:
            sftp.chdir(remotedir)
            return
        except IOError:
            pass

        dirs_to_create = []
        current = remotedir
        while current and current != '/':
            dirs_to_create.insert(0, current)
            current = os.path.dirname(current)

        for dir_path in dirs_to_create:
            try:
                sftp.chdir(dir_path)
            except IOError:
                try:
                    sftp.mkdir(dir_path, mode)
                    sftp.chdir(dir_path)
                except IOError as e:
                    if hasattr(e, 'errno') and e.errno == 17:
                        try:
                            sftp.chdir(dir_path)
                        except IOError:
                            raise IOError(f"Cannot access directory {dir_path}: permission denied")
                    else:
                        raise IOError(f"Cannot create directory {dir_path}: {e}")

    def write_manifest_file(self, manifest_data):
        manifest_file = open(self.base_name + "/manifest.txt", "w")
        manifest_file.write("Date: " + datetime.datetime.now().strftime('%Y%m%d%H%M') + '\n')
        manifest_file.write("MessageCount: " + str(len(manifest_data)) + '\n')

        for message_id in manifest_data:
            manifest_file.write("MessageIds: " + message_id + '\n')

        manifest_file.close()
        log.info("Manifest file completed!!")

    def write_heartbeat_file(self, heartbeat_filename):
        date = datetime.datetime.strftime(datetime.datetime.now(), '%a, %d %b %Y %H:%M:%S')
        heartbeat_date = ["Date: " + date + " -0000"]
        heartbeat_content_prefix = [
            'Content-Type: multipart/alternative; boundary="===============6052643340211323189=="',
            'MIME-Version: 1.0']
        heartbeat_content_suffix = ['From: eightfoldarc@morganstanley.com', 'To: cap.validate@morganstanley.com',
                                    'Message-ID: <Eightfold.heartbeat.message>', 'Subject: Heartbeat for Eightfold', '',
                                    '--===============6052643340211323189==',
                                    'Content-Type: text/html; charset="utf-8"',
                                    'MIME-Version: 1.0', 'Content-Transfer-Encoding: base64', '', 'SGVhcnRiZWF0', '',
                                    '--===============6052643340211323189==--', '']

        heartbeat_content = heartbeat_content_prefix + heartbeat_date + heartbeat_content_suffix
        heartbeat_content = "\n".join(heartbeat_content)

        self.write_to_file(heartbeat_content, heartbeat_filename)

    def get_email_content(self, entity_ids):
        url = 'http://apiv2.eightfold.ai/api/v2/core/user-messages/batch-fetch?include=emailContent'
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'accept': 'application/json'
        }

        email_content_response = []
        for index in range(0, len(entity_ids), 100):
            if index % 1000 == 0:
                log.info("Fetching email content from msg_ids: {} to {}".format(index, index + 99))

            data = {
                'entityIds': entity_ids[index:index + 100]
            }
            time.sleep(1)
            response = requests.post(url, headers=headers, data=json.dumps(data))

            if response and response.status_code == 200:
                email_content_response.extend(response.json().get('data', None))
            else:
                log.info(f'API execution failed with error msg: {response.text}')
                time.sleep(5)

        self.base_name = datetime.datetime.now().strftime('%Y%m%d%H%M') + self.result_filename_prefix
        log.info("***** Total Emails Fetched: {} *****".format(len(email_content_response)))
        os.mkdir(self.base_name)

        manifest_data = []
        filtered_email_cnt = 0
        if email_content_response:
            for entity_changelog in email_content_response:
                if entity_changelog.get('conversationId') == 'contact_reply':
                    email_content = entity_changelog.get('emailContent')
                    if email_content:
                        profile_id = entity_changelog.get('profileId')
                        message_id = entity_changelog.get('id')
                        timestamp = entity_changelog.get('createdAt')
                        if timestamp:
                            timestamp = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H-%M-%S')

                        file_name = profile_id + '_' + message_id + '_' + str(timestamp) + '.eml'
                        self.write_to_file(email_content, file_name)
                        manifest_data.append(file_name)

                        if profile_id not in self.profile_ids:
                            self.profile_ids.append(profile_id)

                        filtered_email_cnt += 1
        else:
            log.info("email_content_response is null")

        log.info("***** Total Emails Filtered: {} *****".format(filtered_email_cnt))

        if filtered_email_cnt == 0:
            heartbeat_filename = "eightfold.heartbeat.eml"
            manifest_data.append(heartbeat_filename)
            self.write_heartbeat_file(heartbeat_filename)
            log.info("Heartbeat file created: {}".format(heartbeat_filename))

        self.write_manifest_file(manifest_data)
        log.info("Completed writing to all the files!!")

    def write_to_csv_file(self, rows):
        file_name = self.mapping_file_name + datetime.datetime.strftime(datetime.date.today(), '%Y-%m-%d') + '.csv'
        local_path = os.path.join(self.base_name, file_name)
        log.info('Writing to mapping file: {}'.format(local_path))
        field_list = ['profile_id', 'candidate_id', 'email', 'first_name', 'last_name']
        with open(local_path, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(field_list)
            for row in rows:
                writer.writerow(row)
        self.transport(local_path, self.host, self.username, self.sftp_path, self.private_key)
        log.info("Mapping file is uploaded!!")
        shutil.rmtree(self.base_name)
        log.info("Mapping file is removed from local path.")

    def build_file_candidate_mapping(self):
        log.info("Now building candidate mapping file...\n")
        log.info("Total unique profiles to be fetched: {}".format(len(self.profile_ids)))
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'accept': 'application/json'
        }

        rows = []
        sleep_count = 0
        for profile_id in self.profile_ids:
            sleep_count += 1
            if sleep_count % 10 == 0:
                log.info("Current fetched profiles count: {}".format(sleep_count))
                time.sleep(5)

            url = f'https://apiv2.eightfold.ai/api/v2/core/profiles/{profile_id}'
            response = requests.get(url, headers=headers)
            if response and not response.json().get('message'):
                data = response.json()
                candidate_id = data.get('atsEntityId', None)
                email = data.get('email')
                first_name = data.get('firstName')
                last_name = data.get('lastName')
                row = [profile_id, candidate_id, email, first_name, last_name]
                rows.append(row)
            else:
                log.info("Not able to fetch data for profile_id: {}".format(profile_id))

        self.write_to_csv_file(rows)

    def calculate_start_end_ts(self, exporter_frequency):
        delta = FREQUENCY.get(exporter_frequency)
        current_time = datetime.datetime.now()
        if delta == 24:
            start_time = current_time - datetime.timedelta(hours=delta)
        else:
            start_time = current_time - datetime.timedelta(days=delta)
        end_ts = current_time.strftime('%s')
        start_ts = start_time.strftime('%s')
        log.info(f'Start TS: {start_ts} and End TS: {end_ts}')
        return start_ts, end_ts


def app_handler(event, context):
    app_settings = event.get('app_settings', {})
    trigger = event.get('trigger_name')
    log.info('Event: {}'.format(str(event)))
    log.info('Context: {}'.format(str(context)))
    group_id = event.get('group_id')
    oauth_username = app_settings.get('oauth_username')
    oauth_password = app_settings.get('oauth_password')

    ef = ApiConnector(oauth_username, oauth_password)
    unconfigured_triggers = []
    for config in app_settings['exporter_config']:
        configured_frequency = config['exporter_frequency']
        if configured_frequency == ConfiguredFrequecy.HOURLY.value and trigger != 'scheduled_hourly' or \
                configured_frequency == ConfiguredFrequecy.DAILY.value and trigger != 'scheduled_daily' or \
                configured_frequency == ConfiguredFrequecy.WEEKLY.value and trigger != 'scheduled_weekly':
            unconfigured_triggers.append({'configured_frequency': configured_frequency, 'triggered_frequency': trigger})
            continue
        for exporter in config['exporter']:
            if exporter not in [e.value for e in SupportedExporters]:
                return _errordict(status_code=500, message='unknown exporter_type'.format(exporter))

        ef.host = config['hostname']
        ef.username = config['username']
        ef.sftp_path = config['sftp_path']
        ef.private_key = config['id_rsa']
        ef.result_filename_prefix = config['result_filename_prefix']
        ef.mapping_file_name = config['mapping_file_name']
        exporter_frequency = config['exporter_frequency']
        start_ts, end_ts = ef.calculate_start_end_ts(exporter_frequency)
        entity_ids = ef.get_message_ids(start_ts, end_ts)
        log.info("***** Total Message IDs found: {} *****".format(str(len(entity_ids))))
        ef.get_email_content(entity_ids)
        ef.zipper(ef.host, ef.username, ef.sftp_path, ef.private_key)
        ef.build_file_candidate_mapping()

    if len(unconfigured_triggers) == len(app_settings['exporter_config']):
        return _successdict(status_code=200,
                            message='Received unconfigured triggers (skipping): {}'.format(unconfigured_triggers))
    return _successdict(status_code=200, message='App invocation successful with {} trigger'.format(trigger))


def main():
    from pprint import pprint

    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
        payload = json.load(f)
    result = app_handler(payload, None)
    print(80 * '~')
    pprint(result)


if __name__ == '__main__':
    main()
