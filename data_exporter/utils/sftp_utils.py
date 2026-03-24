from __future__ import absolute_import

import io
import os
import stat
import tempfile
import traceback

import glog as log
import paramiko

from paramiko.ssh_exception import AuthenticationException
from paramiko.ssh_exception import SSHException
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX


def _load_private_key(private_key_str):
    """
    Load private key from string. Uses pkey directly to avoid paramiko bug
    where key_filename causes RSA keys to be misidentified as DSA
    (ValueError: q must be exactly 160, 224, or 256 bits long).
    """
    key_file = io.StringIO(private_key_str)
    for key_class in (paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey):
        try:
            key_file.seek(0)
            return key_class.from_private_key(key_file)
        except (paramiko.ssh_exception.SSHException, ValueError):
            continue
    raise SFTPException('Could not load private key: unsupported key format')


class CnOpts:
    def __init__(self, knownhosts=None, disable_known_host=True):
        self.log = False
        self.compression = False
        self.ciphers = None
        self.disable_known_host = disable_known_host
        if disable_known_host:
            wmsg = "You will need to explicitly load HostKeys "
            wmsg += "(cnopts.hostkeys.load(filename)) or disable"
            print(EF_DEBUG_LOG_PREFIX + wmsg)
            self.hostkeys = None
        else:
            self.hostkeys = knownhosts

class Sftp:
    def __init__(self, hostname, username, destination, private, working_dir=None, disable_known_host=True):
        self._cnopts = CnOpts(disable_known_host=disable_known_host)
        self._destination = destination
        self._id_path = working_dir or tempfile.mkdtemp()
        self._pkey = _load_private_key(private)

        # Create SSH client and connect
        self._ssh_client = paramiko.SSHClient()
        if self._cnopts.disable_known_host:
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            self._ssh_client.load_system_host_keys()

        self._ssh_client.connect(hostname, username=username, pkey=self._pkey)
        self._connection = self._ssh_client.open_sftp()
        
        self._makedirs(remotedir=self._destination, mode=0o777)
        self._connection.chdir(self._destination)

    def _makedirs(self, remotedir, mode=0o777):
        """
        Create remote directory recursively if it doesn't exist
        """
        if remotedir == '/':
            return

        try:
            self._connection.chdir(remotedir)
            return
        except IOError:
            pass
        dirs_to_create = []
        current_path = remotedir

        while current_path and current_path != '/':
            dirs_to_create.insert(0, current_path)
            current_path = os.path.dirname(current_path)

        for dir_path in dirs_to_create:
            try:
                self._connection.chdir(dir_path)
            except IOError:
                try:
                    self._connection.mkdir(dir_path, mode)
                    self._connection.chdir(dir_path)
                except IOError as e:
                    if hasattr(e, 'errno') and e.errno == 17:
                        try:
                            self._connection.chdir(dir_path)
                        except IOError:
                            raise IOError(f"Cannot access directory {dir_path}: Permission denied")
                    else:
                        raise IOError(f"Cannot create directory {dir_path}: {str(e)}")

    def put(self, *args):
        results = {}
        for file in args:
            try:
                remote_filename = os.path.basename(file)
                self._connection.put(file, remote_filename)
                results[file] = os.stat(file).st_size
            except FileNotFoundError as e:
                log.warn(f'Skip uploading because {str(e)}')
            except OSError as e:
                log.warn(f'Error transferring file {str(e)}')
                results[file] = 0
        return results

    def get_r(self, remotedir, localdir, preserve_mtime=False):
        try:
            if not os.path.exists(localdir):
                os.makedirs(localdir)
            
            for item in self._connection.listdir_attr(remotedir):
                remote_path = os.path.join(remotedir, item.filename)
                local_path = os.path.join(localdir, item.filename)
                
                if stat.S_ISDIR(item.st_mode):
                    self.get_r(remote_path, local_path, preserve_mtime)
                else:
                    self._connection.get(remote_path, local_path)
                    if preserve_mtime:
                        os.utime(local_path, (item.st_atime, item.st_mtime))
            return True
        except Exception as e:
            log.exception(e)
            return False

    def get(self, remotepath, localpath=None, callback=None, preserve_mtime=False):
        try:
            self._connection.get(remotepath, localpath, callback=callback)
            if preserve_mtime:
                remote_stat = self._connection.stat(remotepath)
                os.utime(localpath, (remote_stat.st_atime, remote_stat.st_mtime))
            print(f'{EF_DEBUG_LOG_PREFIX}Successfully load {remotepath} to {localpath}')
            return True
        except FileNotFoundError:
            log.warn(f'Cannot load {remotepath} to {localpath} because file does not exist')
            return False
        except Exception as e:
            log.error(f'Fail to load {remotepath} to {localpath}. Excpetion {str(e)}. Traceback {traceback.format_exc()}')
            return False

    def close(self):
        if self._connection:
            self._connection.close()
        if self._ssh_client:
            self._ssh_client.close()

    __call__ = put


class SFTPException(Exception):
    pass


def verify_sftp_connection(hostname, username, private_key, port=22):
    cnopts = CnOpts(disable_known_host=True)
    pkey = _load_private_key(private_key)

    ssh_client = None
    try:
        ssh_client = paramiko.SSHClient()
        if cnopts.disable_known_host:
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            ssh_client.load_system_host_keys()

        ssh_client.connect(hostname, port=port, username=username, pkey=pkey)
        ssh_client.close()
    except (AuthenticationException, SSHException, PermissionError) as ex:
        if ssh_client:
            ssh_client.close()
        raise SFTPException(f'Error connecting to SFTP server: {str(ex)}')
