import glog as log
import os
import paramiko
import tempfile

class Sftp(object):
    def __init__(self, hostname, username, destination, pub, private):
        self._destination = destination
        self._id_path = tempfile.mkdtemp()
        with open(os.path.join(self._id_path, 'id_rsa.pub'), 'w') as f: f.write(pub)
        with open(os.path.join(self._id_path, 'id_rsa'), 'w') as f: f.write(private)

        log.info(f"Initializing SFTP connection to {hostname} as {username}")

        self._ssh_client = paramiko.SSHClient()
        self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        private_key_path = os.path.join(self._id_path, 'id_rsa')
        private_key = paramiko.RSAKey.from_private_key_file(private_key_path)

        self._ssh_client.connect(hostname=hostname, username=username, pkey=private_key)
        log.info(f"SSH connection established")

        self._connection = self._ssh_client.open_sftp()

        initial_cwd = self._connection.getcwd()
        log.info(f"Initial SFTP working directory: {initial_cwd}")

        log.info(f"Creating/navigating to destination: {self._destination}")
        self._makedirs(self._destination, mode=0o777)

        final_cwd = self._connection.getcwd()
        log.info(f"Final SFTP working directory: {final_cwd}")

    def _makedirs(self, remotedir, mode=0o777):
        log.info(f"_makedirs called with remotedir='{remotedir}'")
        if remotedir == '/':
            self._connection.chdir('/')
            return
        try:
            current_before = self._connection.getcwd()
            log.info(f"Attempting to chdir to '{remotedir}' from '{current_before}'")
            self._connection.chdir(remotedir)
            current_after = self._connection.getcwd()
            log.info(f"Successfully changed to '{current_after}'")
        except IOError as e:
            log.info(f"Directory '{remotedir}' doesn't exist (error: {e}), will create it")
            dirname, basename = os.path.split(remotedir.rstrip('/'))
            log.info(f"Split path: dirname='{dirname}', basename='{basename}'")

            self._makedirs(dirname, mode=mode)

            if basename:
                log.info(f"Creating directory '{basename}'")
                self._connection.mkdir(basename, mode=mode)
                self._connection.chdir(basename)
                log.info(f"Changed to newly created directory: {self._connection.getcwd()}")

    def put(self, *args):
        results = {}
        for file in args:
            try:
                current_dir = self._connection.getcwd()
                basename = os.path.basename(file)
                log.info(f"Uploading '{file}' as '{basename}' to directory '{current_dir}'")
                self._connection.put(file, basename)
                results[file] = os.stat(file).st_size
                log.info(f"Successfully uploaded '{file}' ({results[file]} bytes)")
            except OSError as e:
                log.exception(e)
                results[file] = f'Error transferring file: {e}'
        return results

    __call__ = put
