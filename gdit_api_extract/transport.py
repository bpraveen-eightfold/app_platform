from __future__ import absolute_import

import os
import tempfile
import traceback

import glog as log
import paramiko


class Sftp:
    def __init__(self, hostname, username, destination, pub, private):
        """
        pub      - accepted for backward compatibility but not used;
                   key-based auth only requires the private key.
        private  - PEM-encoded private key as a string.
        """
        self._destination = destination
        self._id_path = tempfile.mkdtemp()
        self._id_private_path = os.path.join(self._id_path, 'id_rsa')

        try:
            with open(self._id_private_path, 'w', encoding='utf_8') as f:
                f.write(private)
            os.chmod(self._id_private_path, 0o600)
        except Exception as ex:
            log.error(f"Error writing private key: {str(ex)}, traceback: {traceback.format_exc()}")

        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(
            hostname,
            username=username,
            key_filename=self._id_private_path,
            look_for_keys=False,
            allow_agent=False,
        )
        self._connection = self._ssh.open_sftp()
        self._makedirs(self._destination, mode=0o777)

    def _makedirs(self, remotedir, mode=0o777):
        """
        Recursively ensure remote directories exist.
        Uses chdir() to probe each path component — avoids the stat()
        permission errors seen on managed SFTP servers (e.g. AWS Transfer
        Family) where intermediate paths are owned by the service.
        """
        if remotedir == '/':
            return

        # Fast path: destination already exists
        try:
            self._connection.chdir(remotedir)
            return
        except IOError:
            pass

        # Walk path components from root → leaf, creating any that are missing
        dirs_to_create = []
        current = remotedir
        while current and current != '/':
            dirs_to_create.insert(0, current)
            current = os.path.dirname(current)

        for dir_path in dirs_to_create:
            try:
                self._connection.chdir(dir_path)
            except IOError:
                try:
                    self._connection.mkdir(dir_path, mode)
                    self._connection.chdir(dir_path)
                except IOError as e:
                    if hasattr(e, 'errno') and e.errno == 17:  # EEXIST — already exists
                        try:
                            self._connection.chdir(dir_path)
                        except IOError:
                            raise IOError(f"Cannot access directory {dir_path}: permission denied")
                    else:
                        raise IOError(f"Cannot create directory {dir_path}: {str(e)}")

    def put(self, *args):
        results = {}
        for file in args:
            remote_filename = os.path.basename(file)
            try:
                self._connection.put(file, remote_filename)
                size = os.stat(file).st_size
                results[file] = size
                log.info(f"SFTP upload successful: {remote_filename} ({size} bytes) → {self._destination}/{remote_filename}")
            except FileNotFoundError as e:
                log.warn(f"Skip uploading, local file not found: {str(e)}")
            except OSError as e:
                log.warn(f"OS error transferring {remote_filename}: {str(e)}")
                results[file] = 0
            except Exception as e:
                log.error(f"Failed to upload {remote_filename}: {str(e)}, traceback: {traceback.format_exc()}")
                results[file] = 0
        return results

    def close(self):
        if self._connection:
            self._connection.close()
        if self._ssh:
            self._ssh.close()

    __call__ = put
