from collections import OrderedDict

import redshift_connector

from utils import time_utils
from db import redshift_constant
from db.table_registry import RedshiftTableRegistry
from incremental_exporter_constants import EF_DEBUG_LOG_PREFIX


def get_db_type_from_tablename(tablename):
    table_class = RedshiftTableRegistry.get_table_class(tablename)
    return table_class().db_type()

def get_cluster_data_from_db_type(db_type, region=None):
    db_type_to_metadata_map = redshift_constant.get_cluster_metadata_map(region)
    cluster_metadata = db_type_to_metadata_map.get(db_type)
    if not cluster_metadata:
        raise Exception(f'Unknown db_type. Supported db_type are {list(db_type_to_metadata_map.keys())}')
    return cluster_metadata

def get_proxy_port_mapping_for_region(region):
    # Since we can connect to the cluster directly, port is always 5439
    return 5439

def contains_sign(text):
    return any(sign in text for sign in ['=', '<', '>', '!'])

def build_select_query(tablename, filter_by, order_by, columns=None):
    cols_clause = ','.join(columns) if columns else '*'
    query = f'SELECT {cols_clause} FROM {tablename}'
    query += ' WHERE '
    where_clause = ' AND '.join(f"{col}'{val}'" if contains_sign(col) else f"{col}='{val}'" for col, val in filter_by.items())
    query += where_clause
    query += f' ORDER BY {order_by}'
    return query

def is_redshift_table(tablename):
    if 'analytics.' in tablename:
        # If there is overlap in tablename, we will specify redshift.<tablename>
        # For example, profile is overlapped in analytics and db entity. Hence, we will put redshift.profiles for analytics one
        tablename = tablename.split('.')[-1]
    return bool(tablename in RedshiftTableRegistry.REDSHIFT_TABLE_CLASS_MAP)
    
class RedshiftClient:

    def __init__(self, user, password, region=None, redshift_host=None):
        self.user = user
        self.password = password
        self.conn = None
        self.region = region
        self.redshift_host = redshift_host

    def _connect(self, db_type, port=None):
        redshift_metadata = get_cluster_data_from_db_type(db_type, region=self.region)
        port = port or get_proxy_port_mapping_for_region(self.region)
        print(f'{EF_DEBUG_LOG_PREFIX}Connecting to {redshift_metadata.host}:{port} on cluster: {redshift_metadata.cluster_identifier} (db_type: {db_type}) as user {self.user}')
        self.conn = redshift_connector.connect(
            host=self.redshift_host or redshift_metadata.host,
            port=port,
            database=db_type,
            cluster_identifier=redshift_metadata.cluster_identifier,
            user=self.user,
            password=self.password,
            ssl=False
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def chunk_load_by_timestamp(self, tablename, lower_bound_ts, upper_bound_ts, filter_by=None, chunk_interval_hours=6, limit=-1, upper_inclusive=False):
        filter_by = filter_by or {}
        table_class = RedshiftTableRegistry.get_table_class(tablename)
        table_obj = table_class()
        timestamp_col = table_obj.timestamp_col() # default is t_create
        num_rows = 0
        chunked_interval = time_utils.create_chunk_timestamp_interval(lower_bound_ts, upper_bound_ts, chunk_interval_hours)
        db_type = get_db_type_from_tablename(tablename)
        user_view = table_obj.get_table_view_name_for_user(self.user)
        for idx, (start_ts, end_ts) in enumerate(chunked_interval):
            my_sql_start_date = time_utils.mysql_timestamp(start_ts)
            my_sql_end_date = time_utils.mysql_timestamp(end_ts)
            filter_by[f'{timestamp_col}>='] = my_sql_start_date
            filter_by[f'{timestamp_col}<=' if idx >= len(chunked_interval) - 1 and upper_inclusive else f'{timestamp_col}<'] = my_sql_end_date
            query = build_select_query(user_view, filter_by, order_by=f'{timestamp_col} DESC')
            all_res = self.get_list(query, db_type=db_type)
            for res in all_res:
                num_rows += 1
                if limit > 0 and num_rows > limit:
                    return
                yield res
        return

    def get_list(self, query, db_type):
        response_list = []
        self._connect(db_type)
        cursor = self.conn.cursor()
        print(f'{EF_DEBUG_LOG_PREFIX}Executing Redshift({db_type}) query: {query}')
        cursor.execute(query)
        headers = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        for res in results:
            row = OrderedDict([(headers[idx], value) for idx, value in enumerate(res)])
            response_list.append(row)
        self.close()
        print(f'{EF_DEBUG_LOG_PREFIX}Receive {len(response_list)} rows from query')
        return response_list

    def _test_connection_query(self, db_type='analytics'):
        table_class = RedshiftTableRegistry.get_table_class('www_server_log')
        tablename = table_class().get_table_view_name_for_user(self.user)
        self.get_list(f'SELECT CURRENT_DATE FROM {tablename} LIMIT 1', db_type=db_type)
