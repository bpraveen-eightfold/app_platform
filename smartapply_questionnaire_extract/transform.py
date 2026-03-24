import datetime
import os
import shutil
import tempfile


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

    def rename_extension_and_move(self, inpath, extension):
        newpath = os.path.splitext(inpath)[0] + '.' + extension
        return shutil.move(inpath, newpath)
