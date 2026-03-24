#!/usr/bin/env python

import glog as log
import json
from pprint import pprint
import traceback
import requests
import time
import datetime
import os
import shutil
import tempfile
import sys
import csv

from constants import URLS, ACCESS_TOKEN_URLS, ACCESS_BASIC_TOKEN
from constants import ConfiguredFrequecy
from constants import SupportedExporters
from transform import ResultXfrm
from transport import Sftp


class InputValidator:
    def __init__(self):
        return


def _errordict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'error': kwargs['message'],
            'stacktrace': traceback.format_exc()
        })
    }


def _successdict(**kwargs):
    return {
        'statusCode': kwargs['status_code'],
        'body': json.dumps({
            'message': kwargs['message']
        })
    }


class ApiConnector:
    def __init__(self, region, oauth_username, oauth_password):
        self.oauth_username = oauth_username
        self.oauth_password = oauth_password
        self.region = region
        self.retry_max_limit = 2
        self.sleep_timer = 5

        if oauth_username and oauth_password:
            self.oauth_data = {
                "grantType": "password",
                "username": self.oauth_username,
                "password": self.oauth_password
            }
            self.oauth_headers = {
                'Authorization': ACCESS_BASIC_TOKEN.get(self.region)
            }

            self.oauth_url = ACCESS_TOKEN_URLS.get(self.region)
            self.access_token = self.generate_access_token()

    def generate_access_token(self):
        retry_cnt = 0
        while retry_cnt <= self.retry_max_limit:
            try:
                log.info(f"Generating Access Token via API URL: {self.oauth_url}")
                response = requests.post(url=self.oauth_url, headers=self.oauth_headers, json=self.oauth_data)
                response.raise_for_status()

                if response and response.json().get('data', {}).get('access_token'):
                    access_token = response.json().get('data', {}).get('access_token')
                    log.info(f"Access token generated: {access_token}\n")
                    return access_token

            except Exception as err:
                log.info(f"API failed with msg: {err}\n")
                retry_cnt += 1
                wait = retry_cnt * self.sleep_timer
                log.info(f"Sleep for {wait} secs and go for retry attempt #{retry_cnt}...\n")
                time.sleep(wait)

        sys.exit(f"** Not able to generate access token. Retry max limit ({self.retry_max_limit}) reached, exiting app!! **\n")

    def get_api_call(self, url):
        retry_cnt = 0
        while retry_cnt <= self.retry_max_limit:
            try:
                headers = {
                    'Authorization': 'Bearer ' + self.access_token,
                    'accept': 'application/json'
                }
                log.info(f"Get API URL: {url}")
                response = requests.get(url=url, headers=headers)
                response.raise_for_status()
                return response.json()

            except Exception as err:
                log.info(f"API failed with msg: {err}\n")
                retry_cnt += 1
                wait = retry_cnt * self.sleep_timer
                log.info(f"Sleep for {wait} secs and go for retry attempt #{retry_cnt}...\n")
                time.sleep(wait)

                if retry_cnt == self.retry_max_limit:
                    log.info("Regenerating access token for last attempt...\n")
                    self.access_token = self.generate_access_token()

        log.info(f"Retry max limit ({self.retry_max_limit}) reached.\n")

    def get_field_data(self, entity_list, field):
        fields = {}
        for entity in entity_list:
            field_data = entity.get(field)
            # try fetching field data from candidateData field, if not available at entity level
            if not field_data and entity.get('candidateData') and entity.get('candidateData', {}).get(field):
                field_data = entity.get('candidateData', {}).get(field)

            if field_data:
                # key = employeeId,email
                ats_id = entity.get('employeeId')
                if field == 'skills' or field == 'resumeFileName':
                    ats_id = entity.get('employeeInfo', {}).get('employeeId')

                ats_id = ats_id if ats_id else ''
                key = ats_id + ',' + entity.get('email')
                fields[key] = field_data

        return fields

    def write_to_file(self, group_id, entity, field, entity_field_data):
        local_path = group_id.split('.')[0] + '_' + entity + '_' + field + '.csv'

        key = list(entity_field_data.keys())[0]
        if isinstance(entity_field_data.get(key), str):
            field_list_without_id = [field]
        else:
            field_list_without_id = list(entity_field_data.get(key)[0].keys())

        field_list = ['id', 'email'] + field_list_without_id
        data_rows = []

        for key, values in entity_field_data.items():
            if values is None:
                continue

            keys = key.split(',', 1)
            id, email = keys[0], keys[-1]

            if isinstance(values, str):
                data_rows.append([id, email, values])
            else:
                for value in values:
                    row = [id, email]
                    for index in field_list_without_id:
                        row.append(value.get(index))
                    data_rows.append(row)

        with open(local_path, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(field_list)
            writer.writerows(data_rows)

        return local_path

    def get_last_modified_ts(self, configured_frequency):
        last_modified_ts = ''
        current_time = datetime.datetime.now()

        if configured_frequency == 'WEEKLY':
            last_modified_ts = current_time - datetime.timedelta(days=7)
        elif configured_frequency == 'DAILY':
            last_modified_ts = current_time - datetime.timedelta(days=1)
        elif configured_frequency == 'HOURLY':
            last_modified_ts = current_time - datetime.timedelta(hours=1)

        log.info(f'Last modified date: {last_modified_ts}')
        return last_modified_ts.strftime('%s')

    def get_data(self, entity, field, region):
        entity_region = entity + '_' + region
        base_url = URLS.get(entity_region)

        # fetch skills or resumeFileName field data from Profile API for employees, since not available in Employee API
        if entity == 'employee' and (field == 'skills' or field == 'resumeFileName'):
            base_url = URLS.get("profile_" + region) + "?filterQuery=employees:*&limit=100&start="
        else:
            base_url = base_url + "?limit=100&start="

        start = 0
        total_records = 1
        field_data = {}

        log.info(f"Fetching data for Entity: **{entity.upper()}** and Field: **{field.upper()}**\n")
        while start < total_records:
            log.info(f"Processing records from {start + 1} to {start + 100}")
            url = base_url + str(start)
            start += 100

            json_response = self.get_api_call(url=url)
            if not json_response:
                log.info("No response from API, moving ahead!!\n")
                continue

            meta_data = json_response.get('meta')
            total_records = int(meta_data.get('totalCount'))
            log.info(f"API response meta data: {meta_data}\n")

            json_data = json_response.get("data")
            if json_data:
                field_data.update(self.get_field_data(json_data, field))

        return field_data if field_data else None


def app_handler(event, context):
    log.info(f'Event: {str(event)}')
    log.info(f'Context: {str(context)}')

    app_settings = event.get('app_settings', {})
    trigger = event.get('trigger_name')
    group_id = event.get('group_id')
    oauth_username = app_settings.get('oauth_username')
    oauth_password = app_settings.get('oauth_password')
    region = app_settings.get('region')

    ef = ApiConnector(region, oauth_username, oauth_password)
    unconfigured_triggers = []
    result_xfrm = ResultXfrm(group_id)
    for config in app_settings['exporter_config']:
        configured_frequency = config['exporter_frequency']
        if configured_frequency == ConfiguredFrequecy.HOURLY.value and trigger != 'scheduled_hourly' or \
                configured_frequency == ConfiguredFrequecy.DAILY.value and trigger != 'scheduled_daily' or \
                configured_frequency == ConfiguredFrequecy.WEEKLY.value and trigger != 'scheduled_weekly':
            unconfigured_triggers.append({'configured_frequency': configured_frequency, 'triggered_frequency': trigger})
            continue
        entity = config.get('entity')
        field = config.get('field')
        for exporter in config['exporter']:
            if exporter not in [e.value for e in SupportedExporters]:
                return _errordict(status_code=500, message='unknown exporter_type'.format(exporter))

        entity_data = ef.get_data(entity, field, region)
        if entity_data:
            log.info("Writing to file...")
            result_location = ef.write_to_file(group_id, entity, field, entity_data)
        else:
            continue

        for transport in config['exporter']:
            if transport == SupportedExporters.SFTP.value:
                s3filename = result_location
                workdir = tempfile.mkdtemp()
                zip_filepath = ''
                metafilepath = None
                # Transform
                localfile = result_xfrm.result_prefix(
                    config.get('result_filename_prefix', '%G.%D.%S'),
                    config.get('result_files_seq_start', '0'),
                    config.get('timestamp_format', '%Y%m%d-%H%M%S'),
                    config.get('suffix', s3filename),
                    config.get('extension', 'csv')
                )
                log.info(f"Extracted filename: {localfile}")
                filepath = os.path.join(workdir, localfile)
                shutil.copyfile(result_location, filepath)
                result_files = [filepath, metafilepath] if metafilepath else [filepath]

                if config.get('zip'):
                    zip_prefix = config.get('result_zip_file_prefix')
                    zip_filename = os.path.splitext(zip_prefix + localfile)[0]
                    indir = os.path.dirname(filepath)
                    zip_filepath = result_xfrm.zipper(zip_filename, indir)
                    result_files.append(zip_filepath)
                    result_files.remove(filepath)
                    result_files.remove(metafilepath)

                # upload to sftp
                Sftp(config['hostname'], config['username'], config['sftp_path'], config['id_rsa.pub'],
                     config['id_rsa']).put(*result_files)

            if zip_filepath:
                shutil.rmtree(os.path.dirname(zip_filepath))
            shutil.rmtree(os.path.dirname(filepath))

    if len(unconfigured_triggers) == len(app_settings['exporter_config']):
        return _successdict(status_code=200, message=f'Received un-configured triggers (skipping): {unconfigured_triggers}')

    return _successdict(status_code=200, message=f'App invocation successful with {trigger} trigger')


def main():
    with open(os.path.join(os.path.dirname(__file__), 'payload.json')) as f:
        payload = json.load(f)

    result = app_handler(payload, None)
    print(80 * '~')
    pprint(result)


if __name__ == '__main__':
    main()
