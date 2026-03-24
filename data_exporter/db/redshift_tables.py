from abc import ABC, abstractmethod
from external_objects.redshift_data_schema import WWWServerLogSchema
from external_objects.redshift_data_schema import UserAnalyticsSchema

class RedshiftTable(ABC):

    @abstractmethod
    def tablename(self):
        pass

    @abstractmethod
    def get_table_view_name_for_user(self, username):
        pass

    @abstractmethod
    def db_type(self):
        pass

    @abstractmethod
    def get_schema_class(self):
        pass

    def timestamp_col(self):
        return 't_create'
    
    def id_col(self):
        return 'id'


##################################
########    Log Table      #######
##################################
class LogTable(RedshiftTable):

    def get_table_view_name_for_user(self, username):
        trimmed_username = username.replace('_user', '')
        return f'{trimmed_username}_logs.{trimmed_username}_{self.tablename()}'

    def db_type(self):
        return 'analytics' # Log table is now moved to analytics db in analytics-consumer cluster
    
class WWWServerLog(LogTable):

    def tablename(self):
        return 'www_server_log'

    def get_schema_class(self):
        return WWWServerLogSchema
    
    def get_table_view_name_for_user(self, username):
        trimmed_username = username.replace('_user', '')
        view_name = self.tablename().replace("www_", "")
        return f'{trimmed_username}_analytics.{trimmed_username}_{view_name}_analytics'

##################################
######    Analytics Table   ######
##################################
class AnalyticsTable(RedshiftTable):

    def get_table_view_name_for_user(self, username):
        trimmed_username = username.replace('_user', '')
        return f'{trimmed_username}_analytics.{trimmed_username}_{self.tablename()}'

    def db_type(self):
        return 'analytics'

class UserAnalytics(AnalyticsTable):

    def tablename(self):
        return 'user_analytics'
    
    def timestamp_col(self):
        return 'timestamp'

    def id_col(self):
        # Return None when there is no ID col present in the table (ex: user_analtyics)
        return None

    def get_schema_class(self):
        return UserAnalyticsSchema
