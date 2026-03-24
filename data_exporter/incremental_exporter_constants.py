DEFAULT_META_EXTENSION = 'meta'

# App state status
PASSED = 'Passed'
FAILED = 'Failed'
PARTIALLY_PASSED = 'Partially Passed'

# App State related key
EXPORTED_TABLES = 'exported_tables'
START_TIME = 'start_time'
END_TIME = 'end_time'
STATUS = 'status'
RECORD_COUNT = 'record_count'
MODIFIED_ENTITIES = 'modified_entities'
MISSING_IDS_FROM_FETCH = 'missing_ids_from_fetch'
FAILED_TO_FETCH_IDS = 'failed_to_fetch_ids'
TO_FETCH_IDS_COUNT = 'to_fetch_ids_count'

# Logging
EF_DEBUG_LOG_PREFIX= '[ef_debug] ' # Prefix for filtering out in user log page

# App Key
APP_KEY = 'incremental_exporter_app'

# filename_format used to generate_output_filename
COMPRESSED_FILE = 'compressed_filename_format'
DATA_FILE = 'data_filename_format'
META_FILE = 'meta_filename_format'

# Schema Version
DEFAULT_SCHEMA_VERSION = 'v1'

# API Server
AUTHORIZATION_TOKEN_MAP = {
    'us-west-2': 'Basic MU92YTg4T1JyMlFBVktEZG8wc1dycTdEOnBOY1NoMno1RlFBMTZ6V2QwN3cyeUFvc3QwTU05MmZmaXFFRDM4ZzJ4SFVyMGRDaw==',
    'eu-central-1': 'Basic Vmd6RlF4YklLUnI2d0tNZWRpdVZTOFhJOmdiM1pjYzUyUzNIRmhsNzd5c2VmNTgyOG5jVk05djl1dGVtQ2tmNVEyMnRpV1VJVQ==',
    'us-gov-west-1': 'Basic UnRRM2NPa1doMlVtVHBHSFlobnl6YnhSOjU1UXcxYXZKclI3VjNRdUMxN2VwSWFadDFEd2hmaG5xempieFE4QlVRMUtFZzFzRg==',
    'ca-central-1': 'Basic Q3hTYzBvaVZuZ2llOFdQMXRsdkxSMlg3OlBJTjVndmRaUVRvc0p3d2Q4SFE1djJMcWNCbVR1d0kybmU5SEU2bFJLT0hLaVNGUw==',
    'me-central-1': 'Basic NHhsY3BWaVRxa2dPMEd6NENCZXFjb3ZWOkI4MEVGT0J3NGx3M0lGbWd2ZUtzU0tMMTZvQ2IxaUM5dUhkcTFEQjVqZ3cwdzZ2Sg=='
}

ACCESS_TOKEN_URL = '/oauth/v1/authenticate'
