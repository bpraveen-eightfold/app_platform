import os

import glog as log

def safe_get_file_size(filename, default=0):
    try:
        return os.path.getsize(filename)
    except FileNotFoundError:
        log.warn(f'Cannot getsize of {filename}')
        return default
