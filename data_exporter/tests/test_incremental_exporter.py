import mock
import os
import unittest

from incremental_exporter import IncrementalExporter
from pathlib import Path
from utils import json_utils
from zipfile import ZipFile

from incremental_exporter_constants import DEFAULT_META_EXTENSION
from incremental_exporter_constants import PASSED
from incremental_exporter_constants import FAILED
from incremental_exporter_constants import PARTIALLY_PASSED
from incremental_exporter_constants import EXPORTED_TABLES
from incremental_exporter_constants import START_TIME
from incremental_exporter_constants import END_TIME
from incremental_exporter_constants import STATUS
from incremental_exporter_constants import RECORD_COUNT
from incremental_exporter_constants import MISSING_IDS_FROM_FETCH
from incremental_exporter_constants import FAILED_TO_FETCH_IDS
from incremental_exporter_constants import TO_FETCH_IDS_COUNT

class FakeResponse:

    def __init__(self, response_json, status_code=200):
        self.response_json = response_json
        self.status_code = status_code

    def json(self):
        return self.response_json

@mock.patch.object(Path, 'mkdir')
class TestIncrementalExporter(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'exporter_config_for_test.json')) as reader:
            exporter_config = json_utils.load(reader)
        
        self.exporter = IncrementalExporter(
            group_id='unittest.com',
            dry_run=False,
            working_dir='/tmp/tmptest',
            start_time=1673913600,
            end_time=1674000000,
            exporter_config=exporter_config,
            last_run_state={
                START_TIME: 1673913600,
                END_TIME: 1674000000,
                EXPORTED_TABLES: {
                    'profiles': {
                        STATUS: PASSED,
                        RECORD_COUNT: 10,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: [],
                        TO_FETCH_IDS_COUNT: 10
                    },
                    'positions': {
                        STATUS: PARTIALLY_PASSED,
                        RECORD_COUNT: 7,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: ['1', '2', '3'],
                        TO_FETCH_IDS_COUNT: 10
                    },
                    'profile-tags': {
                        STATUS: FAILED,
                        RECORD_COUNT: 0,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: ['1', '2', '3'],
                        TO_FETCH_IDS_COUNT: 3
                    }
                    # The test assume we don't have profile-notes state from the last run
                }
            }
        )

    def test_check_last_run_status(self, mock_mkdir):
        exporter = IncrementalExporter(
            group_id='unittest.com',
            dry_run=False,
            working_dir='/tmp/tmptest',
            start_time=1673928005,
            end_time=1674014405,
            exporter_config={},
            last_run_state={
                'start_time': 1673928005,
                'end_time': 1674014405,
                EXPORTED_TABLES: {}
            }
        )
        self.assertTrue(exporter.is_same_run())

        exporter2 = IncrementalExporter(
            group_id='unittest.com',
            dry_run=False,
            working_dir='/tmp/tmptest',
            start_time=1673920005,
            end_time=1674014405,
            exporter_config={},
            last_run_state={
                'start_time': 1673928005,
                'end_time': 1674014405,
                EXPORTED_TABLES: {}
            }
        )
        self.assertFalse(exporter2.is_same_run())

    @mock.patch.object(IncrementalExporter,'compress_data')
    @mock.patch.object(IncrementalExporter,'write_to_storage')
    @mock.patch.object(IncrementalExporter,'write_meta')
    @mock.patch.object(IncrementalExporter,'get_record_count_from_meta', return_value=10)
    @mock.patch.object(IncrementalExporter,'download_last_run_data')
    @mock.patch.object(IncrementalExporter,'chunk_load_data', return_value=2)
    @mock.patch.object(IncrementalExporter,'is_same_run', return_value=False)
    @mock.patch.object(IncrementalExporter, 'fetch_all_ids')
    @mock.patch('db.redshift_utils.is_redshift_table', return_value=False)
    def test_export_data_for_table(self, mock_is_redshift, mock_fetch_all_ids, mock_same_run,
        mock_load, mock_download, mock_get_record_count, mock_write_meta, mock_write_to_storage, mock_compress, mock_mkdir):
        self.exporter.last_run_state = {
            'start_time': 1673827200,
            'end_time': 1674000000,
            EXPORTED_TABLES: {}
        }
        num_processed = self.exporter.export_data_for_table('profiles')
        mock_fetch_all_ids.assert_called_once_with('profiles', start_time=1673913600, end_time=1674000000)
        self.assertTrue(mock_load.called)
        self.assertFalse(mock_download.called)
        self.assertFalse(mock_get_record_count.called)
        self.assertEqual(num_processed, 2)
    
    @mock.patch.object(IncrementalExporter,'compress_data')
    @mock.patch.object(IncrementalExporter,'write_to_storage')
    @mock.patch.object(IncrementalExporter,'write_meta')
    @mock.patch.object(IncrementalExporter,'get_record_count_from_meta', return_value=10)
    @mock.patch.object(IncrementalExporter,'download_last_run_data')
    @mock.patch.object(IncrementalExporter,'chunk_load_data', return_value=2)
    @mock.patch.object(IncrementalExporter,'is_same_run', return_value=False)
    @mock.patch.object(IncrementalExporter, '_save_fetched_ids')
    @mock.patch('db.redshift_utils.is_redshift_table', return_value=False)
    def test_export_data_for_table_recovery_mode(self, mock_is_redshift, mock_save_fetched_ids, mock_same_run,
        mock_load, mock_download, mock_get_record_count, mock_write_meta, mock_write_to_storage, mock_compress, mock_mkdir):
        self.exporter.last_run_state[EXPORTED_TABLES]['profiles'][STATUS] = PARTIALLY_PASSED
        self.exporter.last_run_state[EXPORTED_TABLES]['profiles'][FAILED_TO_FETCH_IDS] = [123, 456]
        num_processed = self.exporter.export_data_for_table('profiles')
        mock_save_fetched_ids.assert_called_once_with([123, 456], 'profiles')
        self.assertTrue(mock_load.called)
        self.assertTrue(mock_download.called)
        self.assertTrue(mock_get_record_count.called)
        self.assertEqual(num_processed, 12)

    def test_get_record_count_from_meta(self, mock_mkdir):
        # self.exporter.merge_recovery_data_with_old_data('profiles')
        with mock.patch('builtins.open', new_callable=mock.mock_open, read_data="resultfile\x01record_count\x01size\ntest_file.json\x0110000\x01123456\n") as mock_open:
            record_count = self.exporter.get_record_count_from_meta('profiles')
            self.assertEqual(record_count, 10000)

    def test_get_output_filename(self, mock_mkdir):
        self.assertEqual(self.exporter.get_output_file_path('profiles'), '/tmp/tmptest/profiles/EFLD.COF.HRDW.PROD.20230117_000000_1_profile.json')
        self.assertEqual(self.exporter.get_meta_file_path('profiles'), '/tmp/tmptest/profiles/EFLD.COF.HRDW.PROD.20230117_000000_1_profile.meta')
        self.assertEqual(self.exporter.get_compress_file_path('profiles'), '/tmp/tmptest/profiles/EFLD.COF.HRDW.PROD.20230117_000000_1_profile.zip')

    @mock.patch.object(IncrementalExporter, 'export_data_for_table', side_effect=[10, 20, 30, 40])
    def test_run_incremental_data_delivery(self, mock_export_data, mock_mkdir):
        _, changelog_size = self.exporter.run_incremental_data_delivery()
        mock_export_data.assert_has_calls([
            mock.call('positions'),
            mock.call('profiles'),
            mock.call('profile-tags'),
            mock.call('profile-notes'),
        ])
        self.assertDictEqual(changelog_size, {'positions': 10, 'profiles': 20, 'profile-tags': 30, 'profile-notes': 40})

class TestIncrementalExporterHttpConnection(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'exporter_config_for_test.json')) as reader:
            exporter_config = json_utils.load(reader)

        self.exporter = IncrementalExporter(
            group_id='unittest.com',
            dry_run=False,
            working_dir='/tmp/tmptest',
            start_time=1673913600,
            end_time=1674000000,
            exporter_config=exporter_config,
            last_run_state={
                'start_time': 1673913600,
                'end_time': 1674000000,
                EXPORTED_TABLES: {
                    'profiles': {
                        STATUS: PASSED,
                        RECORD_COUNT: 0,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: []
                    }
                }
            }
        )

    @mock.patch('utils.thread_utils.parallelize_tasks')
    def test_handle_batch_get_ids_request(self, mock_parallelize_task):
        mock_parallelize_task.side_effect = [
            [FakeResponse({'data': [{'id': 1}]}), FakeResponse({'data': [{'id': 2}]})],
            [FakeResponse({'data': [{'id': 3}]}), FakeResponse({'data': [{'id': 4}]})]
        ]
        resp = self.exporter.handle_batch_get_ids_request('profiles', [1, 2, 3, 4], num_fetch_per_req=1)
        self.assertListEqual(resp, [{'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}])
        mock_parallelize_task.has_called([
            mock.call(
                [
                    {'url': 'https://stage-apiv2.eightfold.ai/api/v2/core/profiles?exclude=tags,resume', 'headers': {'accept': 'application/json', 'Authorization': 'Basic FakeToken'}, 'params': {'profileIds': '1', 'exclude': 'tags,resume'}, 'timeout': 300},
                    {'url': 'https://stage-apiv2.eightfold.ai/api/v2/core/profiles?exclude=tags,resume', 'headers': {'accept': 'application/json', 'Authorization': 'Basic FakeToken'}, 'params': {'profileIds': '2', 'exclude': 'tags,resume'}, 'timeout': 300},
                ],
                mock.ANY, 2
            ),
            mock.call(
                [
                    {'url': 'https://stage-apiv2.eightfold.ai/api/v2/core/profiles?exclude=tags,resume', 'headers': {'accept': 'application/json', 'Authorization': 'Basic FakeToken'}, 'params': {'profileIds': '3', 'exclude': 'tags,resume'}, 'timeout': 300},
                    {'url': 'https://stage-apiv2.eightfold.ai/api/v2/core/profiles?exclude=tags,resume', 'headers': {'accept': 'application/json', 'Authorization': 'Basic FakeToken'}, 'params': {'profileIds': '4', 'exclude': 'tags,resume'}, 'timeout': 300},
                ],
                mock.ANY, 2
            ),
        ])

    @mock.patch('utils.thread_utils.parallelize_tasks')
    def test_handle_batch_get_ids_with_errors(self, mock_parallelize_task):
        mock_response_1 = mock.MagicMock()
        mock_response_1.json.return_value = {'data': [{'id': 1}]}
        mock_response_1.status_code = 200
        mock_response_2 = mock.MagicMock()
        mock_response_2.json.side_effect = Exception('Test Exception')
        mock_parallelize_task.return_value = [mock_response_1, mock_response_2]
        resp = self.exporter.handle_batch_get_ids_request('profiles', [1, 2], num_fetch_per_req=1)
        self.assertListEqual(resp, [{'id': 1}])


class TestIncrementalExporterUtilityFunction(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'exporter_config_for_test.json')) as reader:
            exporter_config = json_utils.load(reader)

        self.exporter = IncrementalExporter(
            group_id='unittest.com',
            dry_run=False,
            working_dir='/tmp/tmptest',
            start_time=1673913600,
            end_time=1674000000,
            exporter_config=exporter_config,
            last_run_state={
                START_TIME: 1673913600,
                END_TIME: 1674000000,
                EXPORTED_TABLES: {
                    'profiles': {
                        STATUS: PASSED,
                        RECORD_COUNT: 10,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: [],
                        TO_FETCH_IDS_COUNT: 10
                    },
                    'positions': {
                        STATUS: PARTIALLY_PASSED,
                        RECORD_COUNT: 7,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: ['1', '2', '3'],
                        TO_FETCH_IDS_COUNT: 10
                    },
                    'profile-tags': {
                        STATUS: FAILED,
                        RECORD_COUNT: 0,
                        MISSING_IDS_FROM_FETCH: [],
                        FAILED_TO_FETCH_IDS: ['1', '2', '3'],
                        TO_FETCH_IDS_COUNT: 3
                    }
                    # The test assume we don't have profile-notes state from the last run
                }
            }
        )

    @mock.patch('zipfile.ZipFile')
    @mock.patch.object(IncrementalExporter, 'get_from_storage')
    def test_download_last_run_data(self, mock_get_from_storage, mock_zipfile):
        self.exporter.download_last_run_data('profiles')
        mock_get_from_storage.assert_called_once_with(
            '/ef-sftp/eightfolddemo-unittest/home/EFLD.COF.HRDW.PROD.20230117_000000_1_profile.zip',
            '/tmp/tmptest/profiles/EFLD.COF.HRDW.PROD.20230117_000000_1_profile.zip'
        )
        # Cannot patch zipfile.ZipFile.extract_all directly since its constructor contains actual file check
        mock_zipfile.return_value.__enter__.return_value.extractall.assert_called_once_with('/tmp/tmptest/profiles')

    def test_instantiate_state(self):
        self.assertDictEqual(
            # Passed state should remain the same
            self.exporter.current_state[EXPORTED_TABLES]['profiles'], 
            {
                STATUS: PASSED,
                RECORD_COUNT: 10,
                MISSING_IDS_FROM_FETCH: [],
                FAILED_TO_FETCH_IDS: [],
                TO_FETCH_IDS_COUNT: 10
            }
        )
        self.assertDictEqual(
            # Partially Passed should reset failed_to_fetch_ids
            self.exporter.current_state[EXPORTED_TABLES]['positions'], 
            {
                STATUS: PARTIALLY_PASSED,
                RECORD_COUNT: 7,
                MISSING_IDS_FROM_FETCH: [],
                FAILED_TO_FETCH_IDS: [],
                TO_FETCH_IDS_COUNT: 10
            }
        )
        self.assertDictEqual(
            # Failed one should all be re-instantiated
            self.exporter.current_state[EXPORTED_TABLES]['profile-tags'], 
            {
                STATUS: None,
                RECORD_COUNT: 0,
                MISSING_IDS_FROM_FETCH: [],
                FAILED_TO_FETCH_IDS: [],
                TO_FETCH_IDS_COUNT: 0
            }
        )
        self.assertDictEqual(
            # Missing / Not previously existed one should all be re-instantiated
            self.exporter.current_state[EXPORTED_TABLES]['profile-notes'], 
            {
                STATUS: None,
                RECORD_COUNT: 0,
                MISSING_IDS_FROM_FETCH: [],
                FAILED_TO_FETCH_IDS: [],
                TO_FETCH_IDS_COUNT: 0
            }
        )

    @mock.patch.object(IncrementalExporter, '_fetch_changelog')
    def test_fetch_all_change_from_changelog(self, mock_fetch_changelog):
        mock_fetch_changelog.side_effect = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            []
        ]
        data = self.exporter.fetch_all_change_from_changelog('profiles', 1673913600, 1674000000, page_size=3, throttle_sec=0)
        self.assertListEqual(data, [1, 2, 3, 4, 5, 6, 7, 8, 9])

