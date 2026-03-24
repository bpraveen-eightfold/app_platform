import glog as log
import json
import os
import pysftp
import tempfile

class Sftp(object):
    def __init__(self, hostname, username, destination, pub, private):
        self._cnopts = pysftp.CnOpts()
        self._cnopts.hostkeys = None
        self._destination = destination
        self._id_path = tempfile.mkdtemp()
        with open(os.path.join(self._id_path, 'id_rsa.pub'), 'w') as f: f.write(pub)
        with open(os.path.join(self._id_path, 'id_rsa'), 'w') as f: f.write(private)
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

class Email(object):
    def __init__(self, From, To):
        self._from = From
        self._to = To

    def put(self, *args):
        # args can be list of links
        for link in args:
            pass
        pass
    __call__ = put

class File(object):
    def __init__(self, From, To):
        self._from = From
        self._to = To

    def put(self, *args):
        data = {'actions': []}
        data['actions'].append({
            'action_name': 'send_email',
            'request_data': {
                'email_from': args[0],
                'email_to': args[1],
                'subject': args[2],
                'body': args[3]
            }
        })
        return {'statusCode': 200, 'body': json.dumps({'data': data})}

    __call__ = put
