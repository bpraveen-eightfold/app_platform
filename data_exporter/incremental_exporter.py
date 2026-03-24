#!/usr/bin/env python
import copy
import datetime
from datetime import datetime as dt
import os
import shutil
import tempfile
import time
import traceback
import zipfile

from pathlib import Path

import glog as log

from data_exporter_utils import NUM_ROWS_TO_FLUSH 
from data_exporter_utils import DownloadFailedExcpetion
from data_exporter_utils import ApiConnector
from db import redshift_utils
from db.table_registry import DBEntityTableRegistry
from db.table_registry import RedshiftTableRegistry
from external_objects import external_objects_utils
from utils import json_utils
from utils import sftp_utils
from utils import str_utils
from utils import thread_utils
from utils import time_utils


from incremental_exporter_constants import PASSED
from incremental_exporter_constants import FAILED
from incremental_exporter_constants import PARTIALLY_PASSED
from incremental_exporter_constants import EXPORTED_TABLES
from incremental_exporter_constants import STATUS
from incremental_exporter_constants import RECORD_COUNT
from incremental_exporter_constants import MISSING_IDS_FROM_FETCH
from incremental_exporter_constants import FAILED_TO_FETCH_IDS
from incremental_exporter_constants import TO_FETCH_IDS_COUNT
from incremental_exporter_constants import MODIFIED_ENTITIES
from incremental_exporter_constants import COMPRESSED_FILE
from incremental_exporter_constants import DATA_FILE
from incremental_exporter_constants import META_FILE
from incremental_exporter_constants import DEFAULT_SCHEMA_VERSION
from incremental_exporter_constants import DEFAULT_META_EXTENSION
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX

from db.table_registry import DerivedTableRegistry
from derived_entity_exporter import export_derived_table

class IncrementalExporter:

    def __init__(self, group_id, dry_run, working_dir=None, start_time=None, end_time=None, exported_limit=-1, overrride_last_run=False, exporter_config=None, last_run_state=None, skip_recovery=False):
        self.group_id = group_id
        self.dry_run = dry_run
        self.working_dir = working_dir or tempfile.mkdtemp()
        self.exported_limit = exported_limit
        self.overrride_last_run = overrride_last_run
        self.exporter_config = exporter_config or {}
        self.redshift_client = redshift_utils.RedshiftClient(exporter_config.get('redshift_user'), exporter_config.get('redshift_password'), exporter_config.get('region'), exporter_config.get('redshift_host'))
        self.last_run_state = last_run_state or {}
        self.current_state = {}
        self.start_time = start_time
        self.end_time = end_time
        self.skip_recovery = skip_recovery
        self._instantiate_state(exporter_config, start_time, end_time)
        self.date_for_file_format = {}
        self.api_connector = ApiConnector(exporter_config.get('api_oauth_username'), exporter_config.get('api_auth_token'), exporter_config.get('api_host'), exporter_config.get('region'))

    def exporter_type(self):
        return 'incremental_data_export'

    ###############################
    ######  Data Fetching     #####
    ###############################

    def _fetch_changelog(self, url, params, timeout=300):
        response = self.api_connector.get_request(url=url, params=params, timeout=timeout)
        response_json = response.json()
        if response.status_code != 200:
            log.error(f'Get status: {response.status_code} with message {response_json} while fetching {url} with params {params}. Exit the fetch for current table')
            raise Exception(f'Get status: {response.status_code} while fetching changelog for the table')
        data = [d.get('entityId') for d in response_json.get('data', [])]
        return data

    def fetch_all_change_from_changelog(self, tablename, start_time, end_time, page_size=10000, throttle_sec=0.75):
        db_class = DBEntityTableRegistry.get_table_class(tablename)
        db_class_obj = db_class()
        url = db_class_obj.change_log_endpoint()
        # TODO - Add back 'limit': page_size once limit is fixed in API Server
        time_interval_list = [(start_time, end_time)] if end_time - start_time <= 86400 else time_utils.create_chunk_timestamp_interval(start_time, end_time, interval_hours=24)
        all_data = []
        for start_time, end_time in time_interval_list:
            param_dict = {'startTime': start_time, 'endTime': end_time, 'start': 0}
            resp_data = []
            resp_data = self._fetch_changelog(url, param_dict)
            all_data += resp_data
            start = 1
            while resp_data:
                # TODO - Add back 'limit': page_size once limit is fixed in API Server
                param_dict = {'startTime': start_time, 'endTime': end_time, 'start': start}
                start_fetch_ts = time.time()
                resp_data = self._fetch_changelog(url, param_dict)
                total_fetch_time = time.time() - start_fetch_ts
                all_data += resp_data
                if self.exported_limit != -1 and len(all_data) >= self.exported_limit:
                    break
                start += 1
                if total_fetch_time < throttle_sec:
                    time.sleep(throttle_sec - total_fetch_time)
            if self.exported_limit != -1 and len(all_data) >= self.exported_limit:
                break
        all_data = all_data[:self.exported_limit] if self.exported_limit != -1 else all_data
        all_data = list(set(all_data)) # Make sure the list is unique
        return all_data

    def fetch_all_ids(self, tablename, start_time, end_time):
        # TODO - Handle Pagination when returned data > 100k
        data = self.fetch_all_change_from_changelog(tablename, start_time, end_time)
        log.info(f'Sucessfully fetch {len(data)} changed ids from {time_utils.mysql_timestamp(start_time)} to {time_utils.mysql_timestamp(end_time)} for {tablename}')
        self._save_fetched_ids(data, tablename)
        self.update_total_num_to_fetch(tablename, len(data))
        return data

    def handle_batch_get_ids_request(self, tablename, to_fetch_id, num_thread=2, num_fetch_per_req=100, throttle_sec=1.5):
        resp = []
        db_class = DBEntityTableRegistry.get_table_class(tablename)
        db_class_obj = db_class()
        url = db_class_obj.batch_get_entity_endpoint()
        if db_class_obj.fields_to_exclude():
            url += f"?exclude={','.join(db_class_obj.fields_to_exclude())}"
        if db_class_obj.fields_to_include():
            include_str = '?include' if not db_class_obj.fields_to_exclude() else '&include'
            url += f"{include_str}={','.join(db_class_obj.fields_to_include())}"
        to_fetch_id = list(set(to_fetch_id)) # Make sure the list is unique
        for i in range(0, len(to_fetch_id), num_fetch_per_req * num_thread):
            # TODO - Add Retry backoff on exceed quota limit. We can inherit Retry from boto_utils
            tasks = []
            total_fetch_current_batch = 0
            for j in range(0, num_thread):
                start_idx = i + num_fetch_per_req * j
                if start_idx >= len(to_fetch_id):
                    break
                ids_to_query = to_fetch_id[start_idx: start_idx + num_fetch_per_req]
                total_fetch_current_batch += len(ids_to_query)
                payload = { 'entityIds': ids_to_query }
                tasks.append({
                    'url': url,
                    'json': payload,
                    'timeout': 300
                })
            if tasks:
                start_fetch_ts = time.time()
                batch_responses = thread_utils.parallelize_tasks(tasks, self.api_connector.post_request, num_threads=len(tasks))
                for idx, response in enumerate(batch_responses):
                    payload = tasks[idx].get('json', {})
                    try:
                        response_json = response.json()
                    except Exception as e:
                        log.warn(f'Fail to parse returned JSON with exception {str(e)}. Traceback: {traceback.format_exc()} when fetching {url} with payload {payload}. Status code: {response.status_code}')
                        response_json = None
                        self.update_failed_to_fetch_ids(tablename, payload.get('entityIds', []))
                        continue

                    if response.status_code != 200:
                        payload = tasks[idx].get('json', {})
                        log.warn(f'Request to {url} with payload {payload} returns with status_code {response.status_code}. Response Content: {response_json}')
                        self.update_failed_to_fetch_ids(tablename, payload.get('entityIds', []))
                        continue

                    data = response_json.get('data', [])
                    resp.extend(data)
                total_fetch_time = time.time() - start_fetch_ts
                print(f'{EF_DEBUG_LOG_PREFIX}Total fetch time for the current batch {total_fetch_time} seconds')
                total_fetch = i + total_fetch_current_batch
                if total_fetch % 1000 == 0 or total_fetch == len(to_fetch_id):
                    log.info(f'Succesully fetch  {total_fetch}/{len(to_fetch_id)} ({total_fetch * 100/(len(to_fetch_id)):.2f}%) for table: {tablename}')
                if total_fetch_time < throttle_sec:
                    # Avoid hitting limit and not to throttle if not neccessary
                    time.sleep(throttle_sec - total_fetch_time)
        return resp

    def _get_missing_ids_from_fetch(self, to_fetch_ids, returned_ids, failed_to_fetch_ids):
        to_fetch_id_set = set([str(eid) for eid in to_fetch_ids])
        failed_to_fetch_id_set = set([str(eid) for eid in failed_to_fetch_ids])
        return to_fetch_id_set.difference(returned_ids.union(failed_to_fetch_id_set))

    def load_data(self, tablename, to_fetch_ids):
        print(f'{EF_DEBUG_LOG_PREFIX}Start loading {len(to_fetch_ids)} items from {tablename} ({self.group_id})')
        db_class_obj = DBEntityTableRegistry.get_table_object(tablename)
        data = self.handle_batch_get_ids_request(tablename, to_fetch_ids, num_fetch_per_req=db_class_obj.batch_fetch_size_per_req())
        data = [external_objects_utils.filter_data_by_schema_version(entity, tablename, self._get_schema_version()) for entity in data if entity.get(db_class_obj.id_col())] # Only return entity with ID
        
        returned_ids = set([str(entity.get(db_class_obj.id_col())) for entity in data])
        missing_ids_from_fetch = self._get_missing_ids_from_fetch(to_fetch_ids, returned_ids, self.get_table_current_state(tablename)[FAILED_TO_FETCH_IDS])
        if missing_ids_from_fetch:
            log.warn(f'Missing ids from fetch {list(missing_ids_from_fetch)}. The data is likely deleted from the system.')
            self.update_missing_ids(tablename, missing_ids_from_fetch)
        print(f'{EF_DEBUG_LOG_PREFIX}Sucessfully loaded: {len(data)} items')
        return data

    def _load_data_and_write_locally(self, tablename, to_fetch_ids):
        data = self.load_data(tablename, to_fetch_ids)
        if not data:
            filename = self.generate_output_filename(tablename, filename_format_cfg_key=DATA_FILE)
            log.warn(f'No data to export for {filename} {self.group_id}')
            return []
        self.write_locally(data, tablename)
        return data

    def get_compress_file_path(self, tablename):
        table_folder = self.get_table_folder_path(tablename)
        return os.path.join(table_folder, self.generate_output_filename(tablename, filename_format_cfg_key=COMPRESSED_FILE))

    def prepare_data_for_export(self, tablename):
        output_file_path = self.get_output_data_file_path(tablename)
        meta_file_path = self.get_meta_file_path(tablename)
        compression_type = self.exporter_config.get('compression_type')
        if compression_type == 'zip':
            compress_output_path = self.get_compress_file_path(tablename)
            return [self.zip_files(compress_output_path, current_file_paths=[output_file_path, meta_file_path])]
        log.warn(f'No compression specified or Unknown compression type: {compression_type}. Return default file data {[output_file_path, meta_file_path]}')
        return [output_file_path, meta_file_path]

    def _create_empty_data_file(self, tablename):
        print(EF_DEBUG_LOG_PREFIX + 'Creating empty data file for export')
        data_file_path = self.get_output_data_file_path(tablename)
        if not os.path.exists(data_file_path):
            with open(data_file_path, mode='w', encoding='utf_8'):
                pass

    def chunk_load_data(self, tablename):
        log.info(f'Start loading all ids for {tablename} ({self.group_id})')
        id_file_name = self.get_id_file_name(tablename)
        file_reader = open(id_file_name, 'r')
        to_fetch_ids = []
        processed_data_id_list = []
        db_class_obj = DBEntityTableRegistry.get_table_object(tablename)
        for line in file_reader:
            to_fetch_ids.append(line.rstrip())
            if to_fetch_ids and len(to_fetch_ids) % NUM_ROWS_TO_FLUSH == 0:
                exported_data = self._load_data_and_write_locally(tablename, to_fetch_ids)
                processed_data_id_list += [d.get(db_class_obj.id_col()) for d in exported_data]
                to_fetch_ids = []
        # Export once more for the rest
        if to_fetch_ids:
            # TODO - handle compress
            exported_data = self._load_data_and_write_locally(tablename, to_fetch_ids)
            processed_data_id_list += [d.get(db_class_obj.id_col()) for d in exported_data]
        file_reader.close()
        log.info(f'Finish loading data and export for {tablename} ({self.group_id}). Total data processed: {len(processed_data_id_list)} items')
        if not processed_data_id_list:
            print(EF_DEBUG_LOG_PREFIX + 'No data was processed')
            self._create_empty_data_file(tablename)
        return processed_data_id_list

    def create_interval_for_redshift_fetch(self, tablename, start_time, end_time):
        fetching_file_name = self.get_id_file_name(tablename)
        with open(fetching_file_name, 'w', encoding='utf_8') as file_writer:
            file_writer.write(f"{start_time},{end_time}\n")
        log.info(f'Finish writing all interval for {tablename} ({self.group_id}) in {fetching_file_name}')

    def _get_export_data_wrapper_as_dict_or_list(self, db_obj_class):
        # If there is no id column, we will append to list instead
        return {} if db_obj_class.id_col() else []

    def chunk_load_data_from_redshift(self, tablename):
        fetching_file_name = self.get_id_file_name(tablename)
        with open(fetching_file_name, 'r', encoding='utf_8') as file_reader:
            line = file_reader.read()
            min_ts, max_ts = line.rstrip().split(',')
        # TODO - Support Offset
        db_class = RedshiftTableRegistry.get_table_class(tablename)
        db_class_obj = db_class()
        to_export_data = []
        processed_entity_list = []
        for data in self.redshift_client.chunk_load_by_timestamp(tablename, min_ts, max_ts, limit=self.exported_limit):
            schema = db_class_obj.get_schema_class()
            external_data = external_objects_utils.filter_data_by_schema_version(schema().dump(data), tablename, self._get_schema_version())
            to_export_data.append(external_data)
        # Export once for every interval
        # TODO - Write last successful interval
        # Note: processed_entity_list will be empty for user_analytics becuase there is no id column in the table
        processed_entity_list = [data.get(db_class_obj.id_col()) for data in to_export_data if data.get(db_class_obj.id_col())]
        self.write_locally(to_export_data, tablename)
        log.info(f'Finish loading data and export for {tablename} ({self.group_id}). Total data processed: {len(to_export_data)} items')
        return processed_entity_list

    ###############################
    ######  Data Uploading   ######
    ###############################
    def save_current_runtime_for_table(self, tablename):
        current_time = time_utils.get_now()
        self.date_for_file_format[tablename] = time_utils.to_datetime(current_time)

    def _get_default_file_suffix(self, filename_format_cfg_key):
        if filename_format_cfg_key == DATA_FILE:
            return self.exporter_config.get('export_data_format')
        elif filename_format_cfg_key == META_FILE:
            return DEFAULT_META_EXTENSION
        elif filename_format_cfg_key == COMPRESSED_FILE:
            return self.exporter_config.get('compression_type')
        return ''

    def generate_output_filename(self, tablename, filename_format_cfg_key):
        """Returns an output filename as string. We support one custom field in output file format

        :param string tablename: A tablename to generate output
        :param string file_type: A tablename to generate output

        The exporter config needs to have the following fileds to custom output name:
            - output_file_formats (required): in the file format you can add the following custom fields
                - output_date_format (optional): This field should be compatible with python standard time format.
                    It is needed only when {output_date_format} is present in output_file_formats ex: testing_file_{output_date_format}.
        """
        file_format = self.exporter_config.get('output_file_formats', {}).get(tablename, {}).get(filename_format_cfg_key)
        date_for_file_format = self.date_for_file_format[tablename]
        if not file_format:
            # Fall back to default naming if the file_format key doesn't present
            dt_str = f'{date_for_file_format.year}_{date_for_file_format.month}_{date_for_file_format.day}'
            return f'{dt_str}_{tablename}.{self._get_default_file_suffix(filename_format_cfg_key)}'
        file_format_params = {}
        if '{output_date_format}' in file_format:
            file_format_params['output_date_format'] = date_for_file_format.strftime(self.exporter_config.get('output_date_format'))
        return file_format.format(**file_format_params)

    def _get_table_object_for_export(self, tablename):
        if tablename in DerivedTableRegistry.DERIVED_TABLE_CLASS_MAP:
            cls = DerivedTableRegistry.DERIVED_TABLE_CLASS_MAP[tablename]
            return cls()
        if tablename in DBEntityTableRegistry.DB_ENTITY_TABLE_CLASS_MAP:
            return DBEntityTableRegistry.get_table_object(tablename)
        if tablename in RedshiftTableRegistry.REDSHIFT_TABLE_CLASS_MAP:
            return RedshiftTableRegistry.get_table_object(tablename)
        return None

    def _convert_list_of_json_to_json(self, tablename, to_export_data):
        """Convert list of records to dict (id-keyed) or list. Supports entity, redshift, and derived tables."""
        table_obj = self._get_table_object_for_export(tablename)
        if table_obj is None:
            return to_export_data
        id_col = table_obj.id_col()
        final_json = {} if id_col else []
        for data in to_export_data:
            if id_col:
                entity_id = data.get(id_col)
                if not entity_id:
                    log.warn(f'Cannot get entity_id for {tablename} with id_col {id_col}. Skip exporting for data: {data}')
                    continue
                final_json[entity_id] = data
            else:
                final_json.append(data)
        return final_json

    def write_json(self, to_export_data, tablename, file_absolute_path):
        """Returns an absolute filename to which data is written. The data format will be {'id1': {json_data}, 'id2': {json_data}}

        :param list to_export_data: A list of JSON for data to be exported.
        :param list file_absolute_path: An absolute path of output file
        """
        with open(file_absolute_path, mode='w', encoding='utf_8') as writer:
            log.info(f'writing {len(to_export_data)} items to {file_absolute_path}')
            final_json = self._convert_list_of_json_to_json(tablename, to_export_data)
            writer.write(json_utils.dumps(final_json, ensure_ascii=False))
        log.info(f'Succesfully writes data as json to {file_absolute_path} locally')
        return file_absolute_path

    def write_jsonline(self, to_export_data, file_absolute_path):
        """Returns an absolute filename to which data is written. The data format will be {json_data}\n{json_data}\n...

        :param list to_export_data: A list of JSON for data to be exported.
        :param list file_absolute_path: An absolute path of output file
        """
        with open(file_absolute_path, mode='a', encoding='utf_8') as writer:
            print(f'{EF_DEBUG_LOG_PREFIX}writing {len(to_export_data)} items to {file_absolute_path}')
            for data in to_export_data:
                writer.write(json_utils.dumps(data, ensure_ascii=False) + '\n')
        print(f'{EF_DEBUG_LOG_PREFIX}Succesfully writes data as jsonl to {file_absolute_path} locally')
        return file_absolute_path

    def get_table_folder_path(self, tablename):
        table_folder = os.path.join(self.working_dir, tablename)
        Path(table_folder).mkdir(parents=True, exist_ok=True) # Safe create
        return table_folder

    def get_output_data_file_path(self, tablename):
        table_folder = self.get_table_folder_path(tablename)
        filename = self.generate_output_filename(tablename, filename_format_cfg_key=DATA_FILE)
        return os.path.join(table_folder, filename)

    def write_locally(self, to_export_data, tablename):
        file_absolute_path = self.get_output_data_file_path(tablename)
        if self.exporter_config.get('export_data_format') == 'json':
            file_absolute_path = self.write_json(to_export_data, tablename, file_absolute_path)
        elif self.exporter_config.get('export_data_format') == 'jsonl':
            file_absolute_path = self.write_jsonline(to_export_data, file_absolute_path)
        else:
            raise Exception(f'Unknown export_data_format {self.exporter_config.get("export_data_format")}')
        return file_absolute_path

    def zip_files(self, output_zip_name, current_file_paths):
        current_file_paths = list(current_file_paths)
        output_zip_name = output_zip_name if output_zip_name.endswith('.zip') else f'{output_zip_name}.zip'
        print(f'{EF_DEBUG_LOG_PREFIX}Start zipping {current_file_paths} to {output_zip_name}')
        with zipfile.ZipFile(output_zip_name, 'w', compression=zipfile.ZIP_DEFLATED) as zip_hander:
            for current_file_path in current_file_paths:
                base_filename = os.path.basename(current_file_path)
                try:
                    zip_hander.write(current_file_path, arcname=base_filename)
                except FileNotFoundError:
                    log.warn(f'Skip writing {current_file_path} because it is not found.')
        return output_zip_name

    def write_to_storage(self, local_path_list):
        # TODO - share with incremental data delivery
        if self.dry_run:
            log.info(f'Skip writing {local_path_list} to storage in dry_run mode')
            return
        destination_path = self.exporter_config.get('destination')
        log.info(f'Start uploading data from {local_path_list} to {destination_path}')
        if self.exporter_config.get('method') == 'sftp':
            sftp_obj = sftp_utils.Sftp(
                hostname=self.exporter_config.get('hostname'),
                username=self.exporter_config.get('username'),
                destination=destination_path,
                private=self.exporter_config.get('private_key'),
                working_dir=self.working_dir
            )
            result_files = local_path_list
            results = sftp_obj.put(*result_files)
            sftp_obj.close()
            log.info(f"Succesfully put object to destination {destination_path}. Result: {results}")

    ###############################
    #####  Data Downloading   #####
    ###############################
    def get_from_storage(self, destination_file_path, local_path):
        result = None
        log.info(f'Start downloading data {destination_file_path} to {local_path}')
        if self.exporter_config.get('method') == 'sftp':
            sftp_obj = sftp_utils.Sftp(
                hostname=self.exporter_config.get('hostname'),
                username=self.exporter_config.get('username'),
                destination=self.exporter_config.get('destination'),
                private=self.exporter_config.get('private_key'),
                working_dir=self.working_dir
            )
            result = sftp_obj.get(destination_file_path, local_path)
            sftp_obj.close()
        return result

    ###############################
    ##  Meta Data File Management #
    ###############################
    def get_meta_file_path(self, tablename):
        table_folder = self.get_table_folder_path(tablename)
        filename = self.generate_output_filename(tablename, filename_format_cfg_key=META_FILE)
        return os.path.join(table_folder, filename)
    
    def _get_delimiter(self):
        return str_utils.safe_unicode_escape(self.exporter_config.get('delimiter', ','))

    def write_meta(self, tablename, entity_id_list):
        # safe_unicode_escape will handle \\x01 from json and convert it to \x01
        output = f'{MODIFIED_ENTITIES}\n'
        output += '\n'.join([str(eid) for eid in entity_id_list])
        meta_file_path = self.get_meta_file_path(tablename)
        with open(meta_file_path, 'w', encoding='utf_8') as file_writer:
            file_writer.write(output)
        return meta_file_path

    def _save_fetched_ids(self, data, tablename):
        id_file_name = self.get_id_file_name(tablename)
        with open(id_file_name, 'w', encoding='utf_8') as file_writer:
            for entity_id in data:
                file_writer.write(f'{entity_id}\n')

    def get_id_file_name(self, tablename):
        return os.path.join(self.working_dir, f'id_list_{tablename}.txt')

    def clean_up_working_dir(self):
        try:
            shutil.rmtree(self.working_dir)
        except Exception as e:
            log.warn(f'Fail to remove {self.working_dir}. Exception {str(e)}. Traceback: {traceback.format_exc()}')

    def _remove_deleted_entities_ids(self, tablename, modified_data_id_list):
        missing_ids = set(self.current_state[EXPORTED_TABLES][tablename].get(MISSING_IDS_FROM_FETCH))
        return [mod_id for mod_id in modified_data_id_list if mod_id not in missing_ids]

    ###############################
    ###  Running Functionality ####
    ###############################
    def export_data_for_table(self, tablename):
        modified_data_id_list = []
        if not self.skip_recovery and self.is_same_run() and self.is_last_run_success(tablename):
            log.info(f'Not running exporting for {tablename} because last run was successful')
            return []

        last_run_status = self.get_last_run_status(tablename)
        self.save_current_runtime_for_table(tablename)
        
        if redshift_utils.is_redshift_table(tablename):
            # TODO - Support partial recovery
            # For Redshift, we currently rerun them all if the last run was not succcess
            self.create_interval_for_redshift_fetch(tablename, start_time=self.start_time, end_time=self.end_time)
            modified_data_id_list = self.chunk_load_data_from_redshift(tablename)
        else:
            if not self.skip_recovery and self.is_same_run() and last_run_status == PARTIALLY_PASSED:
                log.info(f'Rerunning data exporting for {tablename} because the last run was partially success')
                self.write_all_ids_to_fetch_from_last_failed(tablename)
                # Load last run data
                download_success = self.download_last_run_data(tablename)
                if not download_success:
                    raise FileNotFoundError('Cannot download last run data')
                modified_data_id_list = self.get_last_processed_id_list(tablename)
                # Write data on top of last run data
                self.chunk_load_data(tablename)
            else:
                # Fetch all ids when status is failed or it is not run before (None/Unknown) or when we skip_recovery
                modified_data_id_list = self.fetch_all_ids(tablename, start_time=self.start_time, end_time=self.end_time)
                self.chunk_load_data(tablename)
        
        modified_data_id_list = self._remove_deleted_entities_ids(tablename, modified_data_id_list)
        num_processed = len(modified_data_id_list)
        self.write_meta(tablename, entity_id_list=modified_data_id_list)
        self.update_record_count(tablename, num_processed)
        status = self.get_running_status_for_table(tablename)
        if status != PASSED:
            # TODO - until we support partially passed with staging folder, we will mark them as failed
            log.info(f'Skip uploading to storage because current status is not Passed. Current status: {self.get_current_run_status(tablename)}')
            return num_processed
        to_export_file_list = self.prepare_data_for_export(tablename)
        self.write_to_storage(to_export_file_list)
        # Lastly, after writing to storage, update status
        self.update_status(tablename, status)
        return num_processed

    ###############################
    #######  Data Recovery ########
    ###############################
    def get_last_run_folder(self):
        last_run_folder = os.path.join(self.working_dir, 'last_run')
        Path(last_run_folder).mkdir(parents=True, exist_ok=True) # Safe create
        return last_run_folder

    def download_last_run_data(self, tablename):
        log.info('Downloading last run data')
        destination_path = self.exporter_config.get('destination')
        local_compress_output_path = self.get_compress_file_path(tablename)
        # Load to local destination
        destination_compress_file_path = os.path.join(destination_path, self.generate_output_filename(tablename, filename_format_cfg_key=COMPRESSED_FILE))
        download_sucess = self.get_from_storage(destination_compress_file_path, local_compress_output_path)
        if download_sucess:
            log.info(f'Start extracting downloaded data to {local_compress_output_path}')
            with zipfile.ZipFile(local_compress_output_path, 'r') as zip_handler:
                # Extract data to working folder for the current table
                zip_handler.extractall(self.get_table_folder_path(tablename))
            return download_sucess
        raise DownloadFailedExcpetion('Cannot download last run data')

    def get_last_processed_id_list(self, tablename):
        log.info('Reading last run metadata')
        meta_file_path = self.get_meta_file_path(tablename)
        last_entity_id_list = []
        with open(meta_file_path, encoding='utf_8') as reader:
            _ = reader.readline() # pop header out
            for line in reader:
                last_entity_id_list.append(line.strip())
        return last_entity_id_list

    ###############################
    #####  State Management    ####
    ###############################
    def _instantiate_state(self, exporter_config, start_time, end_time):
        self.current_state['start_time'] = start_time
        self.current_state['end_time'] = end_time
        self.current_state[EXPORTED_TABLES] = {}
        export_tables = exporter_config.get('to_export_tables') or []
        derived_tables = exporter_config.get('to_export_derived_tables') or []
        all_exports = export_tables + derived_tables
        for tablename in all_exports:
            table_last_run_state = copy.deepcopy(self._get_tablename_last_state(tablename))
            if not self.skip_recovery and self.is_same_run() and table_last_run_state.get(STATUS) == PASSED:
                print(f'{EF_DEBUG_LOG_PREFIX}Use the same state for {tablename} as last run because it was {PASSED}')
                self.current_state[EXPORTED_TABLES][tablename] = table_last_run_state
            elif not self.skip_recovery and self.is_same_run() and table_last_run_state.get(STATUS) == PARTIALLY_PASSED:
                print(f'{EF_DEBUG_LOG_PREFIX}Use the same state for {tablename} as last run because it was {PARTIALLY_PASSED}')
                self.current_state[EXPORTED_TABLES][tablename] = {
                    **table_last_run_state,
                    FAILED_TO_FETCH_IDS: [] # Reset failed to fetch ids for the current state
                }
            else :
                # If it failed or doesn't have any status or skip recovery. Instantiate from scratch
                print(f'{EF_DEBUG_LOG_PREFIX}Reinstantiate state for {tablename} beucase last state status does not apply. skip_recovery {self.skip_recovery}. is_same_run {self.is_same_run()}. status {table_last_run_state.get(STATUS)}')
                self.current_state[EXPORTED_TABLES][tablename] = {
                    STATUS: None,
                    RECORD_COUNT: 0,
                    MISSING_IDS_FROM_FETCH: [],
                    FAILED_TO_FETCH_IDS: [],
                    TO_FETCH_IDS_COUNT: 0
                }

    def update_status(self, tablename, status):
        log.info(f'Setting status for table: {tablename} to {status}')
        self.current_state[EXPORTED_TABLES][tablename][STATUS] = status

    def get_running_status_for_table(self, tablename):
        current_state = self.get_table_current_state(tablename)
        if current_state[TO_FETCH_IDS_COUNT] == 0:
            # If there is nothing to fetch. Mark as PASSED
            return PASSED
        elif current_state[TO_FETCH_IDS_COUNT] > 0 and len(current_state[FAILED_TO_FETCH_IDS]) == 0:
            # If no failure in fetchin at all. Mark as PASSED
            return PASSED
        elif current_state[TO_FETCH_IDS_COUNT] > 0 and len(current_state[FAILED_TO_FETCH_IDS]) > 0 and len(current_state[FAILED_TO_FETCH_IDS]) < current_state[TO_FETCH_IDS_COUNT]:
            # For PARTIALLY_PASSED, we will mark it as FAILED for now. We will hold this until we implement a staging folder (for reovery) to make PARTIALLY_PASSED works again
            return FAILED
        else:
            # All fetch failed. Mark as FAILED
            return FAILED

    def update_record_count(self, tablename, record_count):
        self.current_state[EXPORTED_TABLES][tablename][RECORD_COUNT] = record_count

    def update_total_num_to_fetch(self, tablename, num_to_fetch):
        self.current_state[EXPORTED_TABLES][tablename][TO_FETCH_IDS_COUNT] += num_to_fetch

    def update_missing_ids(self, tablename, missing_ids):
        missing_ids = list(missing_ids)
        self.current_state[EXPORTED_TABLES][tablename][MISSING_IDS_FROM_FETCH] += missing_ids

    def update_failed_to_fetch_ids(self, tablename, failed_to_fetch_ids):
        failed_to_fetch_ids = list(failed_to_fetch_ids)
        self.current_state[EXPORTED_TABLES][tablename][FAILED_TO_FETCH_IDS] += failed_to_fetch_ids

    def get_table_current_state(self, tablename):
        return self.current_state[EXPORTED_TABLES][tablename]

    def trim_state_for_state_dump(self):
        # Need to trim a few fields for data platform dump because we may exceed maximum data size
        exported_tables = self.current_state.get(EXPORTED_TABLES, {})
        for tablename, table_state in exported_tables.items():
            missing_ids = table_state.get(MISSING_IDS_FROM_FETCH, [])
            if len(missing_ids) > 100:
                print(f'{EF_DEBUG_LOG_PREFIX}Trim sampled missing id from {tablename} missing id from fetch because the current size is more than 100')
            table_state[MISSING_IDS_FROM_FETCH] = missing_ids[:100]
    
    def get_non_passed_status_for_all_tables(self):
        res = {}
        for tablename, table_state in self.current_state.get(EXPORTED_TABLES, {}).items():
            status = table_state.get(STATUS)
            if status != PASSED:
                res[tablename] = status or FAILED  # Treat None as fail for output
        return res

    ###############################
    #### Checkpoint  Management ###
    ###############################
    def _get_tablename_last_state(self, tablename):
        return self.last_run_state.get(EXPORTED_TABLES, {}).get(tablename, {})

    def is_same_run(self):
        return self.last_run_state.get('start_time') == self.current_state.get('start_time') and self.last_run_state.get('end_time') == self.current_state.get('end_time')

    def is_last_run_success(self, tablename):
        table_last_run_state = self._get_tablename_last_state(tablename)
        return bool(table_last_run_state.get(STATUS) == PASSED)

    def get_last_run_status(self, tablename):
        table_last_run_state = self._get_tablename_last_state(tablename)
        return table_last_run_state.get(STATUS)

    def get_current_run_status(self, tablename):
        table_current_state = self.current_state.get(EXPORTED_TABLES, {}).get(tablename, {})
        return table_current_state.get(STATUS)
        
    def write_all_ids_to_fetch_from_last_failed(self, tablename):
        last_state = self._get_tablename_last_state(tablename)
        data = last_state.get(FAILED_TO_FETCH_IDS, [])
        self._save_fetched_ids(data, tablename)

    ###############################
    ######## Schema Control #######
    ###############################
    def _get_schema_version(self):
        # Currently default to v1. We shall update this field if we want to update default fields
        return self.exporter_config.get('schema_version', DEFAULT_SCHEMA_VERSION)
    
    ###############################
    ######## Running App ##########
    ###############################
    def should_delivery_now(self):
        delivery_time = self.exporter_config.get('delivery_time')
        if not delivery_time:
            # If this value is not set, start anytime of the day
            log.info('Delivery time is not set. Data export should start now')
            return True
        delivery_time_obj = time_utils.parse_time_str_for_today(delivery_time)
        current_time = time_utils.get_now()
        log.info(f'Checking delivery time. Current Time: {current_time}. Delivery Time: {delivery_time_obj}')
        return current_time >= delivery_time_obj
        
    def run_incremental_data_delivery(self):
        if not self.should_delivery_now():
            log.info('Skip running incremental exporter because delivery time requirement is not met. Revert current_state to last_run_state')
            self.current_state = self.last_run_state
            return {}, {}

        to_export_tables = self.exporter_config.get('to_export_tables') or []
        to_export_derived_tables = self.exporter_config.get('to_export_derived_tables') or []
        run_time = {}
        changelog_size = {}
        for tablename in to_export_tables:
            try:
                st = time.time()
                num_changelog = self.export_data_for_table(tablename)
                run_time[tablename] = time.time() - st
                changelog_size[tablename] = num_changelog
            except DownloadFailedExcpetion as ex:
                log.error(f'Last run data is not downloaded. Skip recovering {tablename}')
            except Exception as ex:
                log.error(f'Failed to export data for {tablename}. {str(ex)}. Stacktrace: ({traceback.format_exc()}).')
        for name in to_export_derived_tables:
            try:
                st = time.time()
                derived_table = DerivedTableRegistry.get_derived_table_object(name)
                if derived_table:
                    num_changelog = export_derived_table(derived_table, self)
                else:
                    log.error(f'Unknown derived table: {name}')
                    continue
                run_time[name] = time.time() - st
                changelog_size[name] = num_changelog
            except Exception as ex:
                log.error(f'Failed to export derived {name}. {str(ex)}. Stacktrace: ({traceback.format_exc()}).')
        return run_time, changelog_size

def get_running_interval(start_date=None, days=1):
    # Assumption here is that endtime will be the current day 00:00 AM
    days = str_utils.safe_get_int(days) if days else 1
    if not start_date:
        end_date = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - datetime.timedelta(days)
    else:
        start_date = time_utils.date_obj_from_str(start_date)
        end_date = start_date + datetime.timedelta(days)
    return int(time_utils.to_timestamp(start_date)), int(time_utils.to_timestamp(end_date))
