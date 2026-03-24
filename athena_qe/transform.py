from botocore.exceptions import ClientError

import datetime
import os
import glog as log
import pandas
import shutil
import tempfile
import gnupg

from constants import RESULT_FIELD_DEFAULT_DELIMITER
from constants import EncryptionAlgorithm
from constants import Constants 

class ResultXfrm(object):
    def __init__(self, group_id):
        self._group_id = group_id

    def zipper(self, outfilename:str, indir:str)->str:
        assert not outfilename.endswith('.zip') == True
        assert indir.startswith('/') == True
        workdir = tempfile.mkdtemp()
        shutil.make_archive(os.path.join(workdir, outfilename), 'zip', indir)
        return os.path.join(workdir, outfilename) + '.zip'

    def result_prefix(self, formatter, seq, dateformat, suffix='', extension='.csv'):
        prefix = ''
        for token in formatter.split('%'):
            if token and token[0] in 'GDS':
                if token[0] == 'G':
                    prefix += self._group_id
                if token[0] == 'D':
                    prefix += datetime.datetime.utcnow().strftime(dateformat)
                if token[0] == 'S':
                    prefix += str(seq)
                prefix += token[1:]
            else:
                prefix += token
        return prefix + suffix + '.' + extension

    def generate_metafile(self, filepath, encrypt=False) -> str:
        buf = pandas.read_csv(filepath)
        buf.to_csv(filepath, sep=RESULT_FIELD_DEFAULT_DELIMITER, index=False) 
        num_rows = len(buf)
        metafile = os.path.splitext(filepath)[0] + '.meta'
        result_file = os.path.basename(filepath) + '.gpg' if encrypt else os.path.basename(filepath)
        df = pandas.DataFrame({'resultfile': [result_file], 'record_count': [num_rows], 'size':  [os.stat(filepath).st_size]})
        df.to_csv(metafile, index=False, sep= RESULT_FIELD_DEFAULT_DELIMITER)
        return metafile
    
    def change_sep(self, filepaths, *args):
        for filepath in filepaths:
            buf = pandas.read_csv(filepath)
            buf.to_csv(filepath, sep=args[0], index=False)

    def sign_url(self, src):      
        src = src[len('s3://'):]
        bucket = src.split('/', 1)[0]
        obj = src.split('/', 1)[1]
        try:
            response = Constants.s3_client.generate_presigned_url('get_object', Params={ 'Bucket': bucket, 'Key': obj}, ExpiresIn=3600 * 24 * 7)
        except ClientError as e:
            log.error(e)
            return None
        return response
    def rename_extension_and_move(self, inpath, extension):
        newpath = os.path.splitext(inpath)[0] + '.' + extension
        return shutil.move(inpath, newpath)

    def remove_header(self, result_files, separator):
        for filepath in result_files:
            buf = pandas.read_csv(filepath, sep=separator)
            buf.to_csv(filepath, sep=separator, header=False, index=False)

    def encrypt_files(self, result_files, encryption_public_key, recipients):
        encrypted_files = []
        for file in result_files:
            os.environ["LD_LIBRARY_PATH"] = './'
            os.environ["HOME"] = '/tmp'
            gpg = gnupg.GPG(gnupghome='/tmp', gpgbinary='./gpg')
            output_file_name = '{}.gpg'.format(file)
            log.info(f'output_file_name: {output_file_name}')
            res = gpg.import_keys(encryption_public_key)
            log.info(f'import keys result: {res.__dict__}')
            with open(file, 'rb') as f:
                res = gpg.encrypt_file(f, recipients, always_trust=True, output=output_file_name)
                log.info(f'encrypt file result: {res.__dict__}')
            encrypted_files.append(output_file_name)
        return encrypted_files
