import glog as log
import time
from constants import Constants

class QueryExecutor(object):
    def __init__(self, athena_client):
        self.athena_client = athena_client
    
    def execute(self, query, timeout=900)->dict:
        try:
            response = Constants.athena_client.start_query_execution(QueryString=query,
                    QueryExecutionContext={
                        'Database': Constants.dbname,
                        'Catalog': 'AwsDataCatalog'
                    },
                    WorkGroup=Constants.workgroup)
        except:
            # Retry once with fallback_db
            response = Constants.athena_client.start_query_execution(QueryString=query,
                    QueryExecutionContext={
                        'Database': Constants.fallback_dbname,
                        'Catalog': 'AwsDataCatalog'
                    },
                    WorkGroup=Constants.workgroup)
        query_id = response.get('QueryExecutionId')

        state = 'QUEUED'
        sleep_for = 1
        total_time = 0
        while state != 'SUCCEEDED' and total_time <= timeout:
            time.sleep(sleep_for)
            total_time += sleep_for
            sleep_for = sleep_for << 1

            info = Constants.athena_client.get_query_execution(QueryExecutionId=query_id)
            state = info['QueryExecution']['Status']['State']

            if state in ['FAILED', 'CANCELLED']:
                log.error('Query {} : ID {} failed, state {}'.format(query, query_id, state))
                return None

        if total_time > timeout:
            return None

        Constants.athena_client.get_query_results(QueryExecutionId=query_id)
        return info['QueryExecution']['ResultConfiguration']['OutputLocation']
    __call__  = execute     