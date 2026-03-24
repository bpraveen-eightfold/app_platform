import mock
import unittest

from external_objects import external_objects_utils

class TestDBEntityTable(unittest.TestCase):

    @mock.patch('external_objects.external_objects_utils.get_data_schema_version')
    def test_filter_data_by_schema_version(self, mock_get_data_schema_version):
        mock_get_data_schema_version.return_value = {
            'profiles': ['id', 'f1', 'f2']
        }

        data = {'id': 123, 'f1': 10, 'f2': 20, 'f3': 100}
        filtered_data = external_objects_utils.filter_data_by_schema_version(data, 'profiles', 'v1')
        self.assertDictEqual(filtered_data, {'id': 123, 'f1': 10, 'f2': 20})
        
    @mock.patch('external_objects.external_objects_utils.get_data_schema_version')
    def test_filter_data_by_schema_version_table_not_found(self, mock_get_data_schema_version):
        mock_get_data_schema_version.return_value = {
            'profiles': ['id', 'f1', 'f2']
        }

        data = {'id': 123, 'f1': 10, 'f2': 20, 'f3': 100}
        filtered_data = external_objects_utils.filter_data_by_schema_version(data, 'positions', 'v1')
        self.assertDictEqual(filtered_data, {'id': 123, 'f1': 10, 'f2': 20, 'f3': 100})

    @mock.patch('external_objects.external_objects_utils.get_data_schema_version')
    def test_filter_data_when_schema_has_extra_fields(self, mock_get_data_schema_version):
        mock_get_data_schema_version.return_value = {
            'profiles': ['id', 'f1', 'f2', 'f10']
        }

        data = {'id': 123, 'f1': 10, 'f2': 20, 'f3': 100}
        filtered_data = external_objects_utils.filter_data_by_schema_version(data, 'profiles', 'v1')
        self.assertDictEqual(filtered_data, {'id': 123, 'f1': 10, 'f2': 20, 'f10': None})
