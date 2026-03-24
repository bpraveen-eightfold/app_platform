import traceback
from multiprocessing.dummy import Pool as ThreadPool

import glog as log

def parallelize_tasks(tasks, func, num_threads=4):
    if not tasks:
        return []

    if len(tasks) == 1:
        return [func(**tasks[0])]

    assert num_threads
    log.debug('{} tasks, running in pool with {} threads'.format(len(tasks), num_threads))
    pool = ThreadPool(num_threads)
    # wrap to print exceptions with correct traceback
    def invoker_func(**args):
        try:
            return func(**args)
        except:
            log.error(f"Exception executing thread func {traceback.format_exc()}")
            raise
    results = pool.map(lambda args: invoker_func(**args), tasks)

    pool.close()
    pool.join()

    return results
