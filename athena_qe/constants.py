from enum import Enum
import boto3

from botocore.client import Config

class FieldSeps(Enum):
    COMMA = ','
    PIPE = '|'
    CTRL_A = '\001'
RESULT_FIELD_DEFAULT_DELIMITER=FieldSeps.COMMA.value
field_separators = {'CTRL-A': FieldSeps.CTRL_A.value, '|' : FieldSeps.PIPE.value, ',': FieldSeps.COMMA.value}

class MetaExtension(Enum):
    META = 'meta'
class SupportedExporters(Enum):
    SFTP = 'sftp'
    EMAIL = 'email'
    FILE = 'file'

class ConfiguredFrequecy(Enum):
    HOURLY = 'HOURLY'
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'

class EncryptionAlgorithm(Enum):
    CAST5 = 'cast5'
    AES256 = 'aes256'

class Constants:
    ''' contants for a group_id, or system level.'''
    MAX_NAME_LEN = 128
    ATHENA_PREFIX = 'athena-'
    @staticmethod
    def normalize_group_id(group_id):
        group_id = group_id.replace('eightfolddemo', 'efdemo')
        if not group_id[0].isalpha():
            group_id = 'g_' + group_id
        parts = group_id.split('.')
        group_id = '-'.join(parts[0:-1] if len(parts) else [group_id])
        return ''.join(c for c in group_id if c.isalnum() or c in ['-', '_'])
    
    @staticmethod
    def get_prefix_for_group_id(group_id):
        group_id = group_id.replace('eightfolddemo', 'efdemo')
        if not group_id[0].isalpha():
            group_id = 'g_' + group_id
        group_id = group_id[0:group_id.rfind('.')] if '.' in group_id else group_id
        return group_id.replace('-', '_').replace('.', '')[:Constants.MAX_NAME_LEN]
    
    group_id, workgroup, dbname, fallback_dbname, aws_access_key_id, aws_secret_access_key, region, athena_client, s3_client = [None] * 9
    def __init__(self, group_id, aws_access_key_id, aws_secret_access_key, region):
        Constants.group_id = Constants.normalize_group_id(group_id)
        Constants.workgroup = Constants.ATHENA_PREFIX + Constants.group_id + '-workgroup'
        Constants.dbname = '{}_db'.format(Constants.get_prefix_for_group_id(Constants.group_id))
        Constants.fallback_dbname = Constants.ATHENA_PREFIX + Constants.get_prefix_for_group_id(Constants.group_id) + '-database'
        Constants.aws_access_key_id = aws_access_key_id
        Constants.aws_secret_access_key =aws_secret_access_key
        Constants.region = region
        Constants.athena_client = boto3.client('athena', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region)
        Constants.s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id,  aws_secret_access_key=aws_secret_access_key, region_name=region, config=Config(signature_version='s3v4'))
