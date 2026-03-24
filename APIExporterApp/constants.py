from enum import Enum


class SupportedExporters(Enum):
    SFTP = 'sftp'
    EMAIL = 'email'
    FILE = 'file'


class ConfiguredFrequecy(Enum):
    HOURLY = 'HOURLY'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


class FieldSeps(Enum):
    COMMA = ','
    PIPE = '|'
    CTRL_A = '\001'


RESULT_FIELD_DEFAULT_DELIMITER = FieldSeps.COMMA.value
field_separators = {'CTRL-A': FieldSeps.CTRL_A.value, '|': FieldSeps.PIPE.value, ',': FieldSeps.COMMA.value}


class MetaExtension(Enum):
    META = 'meta'


URLS = {
    'profile_us': 'https://apiv2.eightfold.ai/api/v2/core/profiles',
    'employee_us': 'https://apiv2.eightfold.ai/api/v2/core/employees',
    'user_us': 'https://apiv2.eightfold.ai/api/v2/core/users',
    'profile_eu': 'https://apiv2.eightfold-eu.ai/api/v2/core/profiles',
    'employee_eu': 'https://apiv2.eightfold-eu.ai/api/v2/core/employees',
    'user_eu': 'https://apiv2.eightfold-eu.ai/api/v2/core/users',
    'profile_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/profiles',
    'employee_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/employees',
    'user_gov': 'https://apiv2.eightfold-gov.ai/api/v2/core/users'
}

ACCESS_TOKEN_URLS = {
    'us': 'https://apiv2.eightfold.ai/oauth/v1/authenticate',
    'eu': 'https://apiv2.eightfold-eu.ai/oauth/v1/authenticate',
    'gov': 'https://apiv2.eightfold-gov.ai/oauth/v1/authenticate'
}

ACCESS_BASIC_TOKEN = {
    'us': 'Basic MU92YTg4T1JyMlFBVktEZG8wc1dycTdEOnBOY1NoMno1RlFBMTZ6V2QwN3cyeUFvc3QwTU05MmZmaXFFRDM4ZzJ4SFVyMGRDaw==',
    'eu': 'Basic Vmd6RlF4YklLUnI2d0tNZWRpdVZTOFhJOmdiM1pjYzUyUzNIRmhsNzd5c2VmNTgyOG5jVk05djl1dGVtQ2tmNVEyMnRpV1VJVQ==',
    'gov': 'Basic UnRRM2NPa1doMlVtVHBHSFlobnl6YnhSOjU1UXcxYXZKclI3VjNRdUMxN2VwSWFadDFEd2hmaG5xempieFE4QlVRMUtFZzFzRg=='
}
