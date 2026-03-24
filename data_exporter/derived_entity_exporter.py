"""
Derived entity export flow: parent changelog -> fetch parents -> extract -> write.
Parallel to incremental_exporter for primary tables. Called from incremental
exporter or lambda when derived_tables is configured.
"""

from __future__ import absolute_import

import os
import time
import traceback

import glog as log

from db.table_registry import DBEntityTableRegistry
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX
from incremental_exporter_constants import EXPORTED_TABLES
from incremental_exporter_constants import FAILED
from incremental_exporter_constants import MISSING_IDS_FROM_FETCH
from incremental_exporter_constants import PASSED
from incremental_exporter_constants import RECORD_COUNT
from incremental_exporter_constants import STATUS
from incremental_exporter_constants import TO_FETCH_IDS_COUNT

CHANGELOG_PAGE_SIZE = 100
BATCH_SIZE = 100
THROTTLE_SEC = 1.5


def _fetch_changelog_page(api_connector, parent_table, start_time, end_time, start, limit):
    db_class = DBEntityTableRegistry.get_table_class(parent_table)
    url = db_class().change_log_endpoint()
    params = {
        'startTime': str(start_time),
        'endTime': str(end_time),
        'start': start,
        'limit': limit,
    }
    response = api_connector.get_request(url=url, params=params, timeout=300)
    data = response.json()
    if response.status_code != 200:
        raise Exception(f'Changelog failed: {response.status_code} - {data}')
    return [d.get('entityId') for d in data.get('data', [])]


def _batch_fetch_parents(api_connector, parent_table, entity_ids, include_fields):
    """Fetch parent entities in batches. Returns (data_list, failed_to_fetch_ids)."""
    db_class = DBEntityTableRegistry.get_table_class(parent_table)
    obj = db_class()
    url = obj.batch_get_entity_endpoint()
    if obj.fields_to_exclude():
        url += f"?exclude={','.join(obj.fields_to_exclude())}"
    include = list(obj.fields_to_include()) + list(include_fields)
    if include:
        sep = '&' if obj.fields_to_exclude() else '?'
        url += f"{sep}include={','.join(include)}"
    result = []
    failed_to_fetch_ids = []
    for i in range(0, len(entity_ids), BATCH_SIZE):
        batch = entity_ids[i:i + BATCH_SIZE]
        resp = api_connector.post_request(url=url, json={'entityIds': batch}, timeout=300)
        try:
            if resp.status_code != 200:
                log.warn(f'Batch fetch: status={resp.status_code}, batch size={len(batch)}')
                failed_to_fetch_ids.extend(batch)
                continue
            data = resp.json().get('data', [])
            result.extend(data)
        except Exception as e:
            log.warn(f'Batch fetch parse error: {e}')
            failed_to_fetch_ids.extend(batch)
        if (i + BATCH_SIZE) < len(entity_ids):
            time.sleep(THROTTLE_SEC)
    return result, failed_to_fetch_ids


def export_derived_table(derived_table, exporter):
    """
    Generic flow: parent changelog -> fetch parents -> extract -> write.
    :param derived_table: DerivedTable instance
    :param exporter: IncrementalExporter
    :return: Record count
    """
    name = derived_table.tablename()
    parent_table = derived_table.parent_table()
    start_time = exporter.start_time
    end_time = exporter.end_time
    parent_id_col = DBEntityTableRegistry.get_table_class(parent_table)().id_col()
    derived_table_id_col = derived_table.id_col()


    if not exporter.skip_recovery and exporter.is_same_run() and exporter.is_last_run_success(name):
        log.info(f'Not running exporting for {name} because last run was successful')
        last_state = exporter._get_tablename_last_state(name)
        return last_state.get(TO_FETCH_IDS_COUNT, 0)

    try:
        log.info(f'Starting derived export {name} (parent: {parent_table})')
        record_ids = []
        total_record_count = 0
        missing_ids = []
        total_parents = 0
        start = 0

        exporter.save_current_runtime_for_table(name)

        while True:
            entity_ids = _fetch_changelog_page(
                exporter.api_connector, parent_table, start_time, end_time, start, CHANGELOG_PAGE_SIZE
            )
            if not entity_ids:
                break

            parents, batch_failed = _batch_fetch_parents(
                exporter.api_connector, parent_table, entity_ids, derived_table.include_fields()
            )
            if batch_failed:
                exporter.update_failed_to_fetch_ids(name, batch_failed)
            returned = {str(p.get(parent_id_col)) for p in parents if p.get(parent_id_col)}
            missing_ids.extend(eid for eid in entity_ids if eid not in returned)

            batch_records = []
            for parent in parents:
                batch_records.extend(derived_table.extract(parent, start_time, end_time))

            if batch_records:
                exporter.write_locally(batch_records, name)
            if derived_table_id_col:
                record_ids.extend(r[derived_table_id_col] for r in batch_records if r.get(derived_table_id_col))
            total_record_count += len(batch_records)

            total_parents += len(entity_ids)
            start += len(entity_ids)
            time.sleep(THROTTLE_SEC)

        log.info(f'Processed {total_parents} parents, extracted {total_record_count} records')

        if not total_record_count:
            exporter._create_empty_data_file(name)
        data_path = exporter.get_output_data_file_path(name)
        exporter.write_meta(name, entity_id_list=record_ids)

        log.info(f'Wrote {total_record_count} records to {data_path}')
        print(f'{EF_DEBUG_LOG_PREFIX}Data file: {os.path.abspath(data_path)}')
        print(f'{EF_DEBUG_LOG_PREFIX}Meta file: {os.path.abspath(exporter.get_meta_file_path(name))}')

        exporter.current_state[EXPORTED_TABLES][name].update({
            RECORD_COUNT: total_record_count,
            MISSING_IDS_FROM_FETCH: missing_ids,
            TO_FETCH_IDS_COUNT: total_parents,
        })
        status = exporter.get_running_status_for_table(name)
        exporter.update_status(name, status)

        if status != PASSED:
            log.info(f'Skip uploading to storage for {name} because status is not Passed. Current status: {status}')
        elif not exporter.dry_run:
            to_export_files = exporter.prepare_data_for_export(name)
            exporter.write_to_storage(to_export_files)

        return total_record_count

    except Exception as ex:
        log.error(f'Derived export {name} failed: {ex}\n{traceback.format_exc()}')
        exporter.current_state[EXPORTED_TABLES][name][STATUS] = FAILED
        raise
