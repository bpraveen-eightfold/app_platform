import glog as log
import os
import pysftp
import tempfile


class Sftp:
    def __init__(self, hostname, username, destination, private):
        self._cnopts = pysftp.CnOpts()
        self._cnopts.hostkeys = None
        self._destination = destination
        self._id_path = tempfile.mkdtemp()
        with open(os.path.join(self._id_path, 'id_rsa'), 'w', encoding='utf_8') as f: f.write(private)
        self._connection = pysftp.Connection(hostname, username=username, private_key=os.path.join(self._id_path, 'id_rsa'),cnopts=self._cnopts)
        self._connection.makedirs(remotedir=self._destination, mode=777)
        self._connection.chdir(remotepath=self._destination)

    def put(self, *args):
        results = {}
        for file in args:
            try:
                self._connection.put(file)
                results[file] = os.stat(file).st_size
            except OSError as e:
                status_code = 500
                log.exception(e)
                results[file] = f'Error transferring file {str(e)}'
        return results
    __call__ = put
