# Entity Table
from db.db_entity_tables import Profile
from db.db_entity_tables import Position
from db.db_entity_tables import PorfileApplication
from db.db_entity_tables import ProfileTag
from db.db_entity_tables import ProfileNote
from db.db_entity_tables import ProfileFeedback
from db.db_entity_tables import PlannedEvent
from db.db_entity_tables import UserCampaign
from db.db_entity_tables import UserMessage
from db.db_entity_tables import EventCandidateActivity
from db.db_entity_tables import User
from db.db_entity_tables import EmailDeliveryFeedback
from db.db_entity_tables import UserCalendarEvent
from db.db_entity_tables import Employee
# Redshift Table
from db.redshift_tables import WWWServerLog
from db.redshift_tables import UserAnalytics

# Derived Table
from db.derived_entity_tables import JtnFormSubmissionsTable

class UnknownTableException(Exception):
    pass

class DBEntityTableRegistry:

    DB_ENTITY_TABLE_LIST = [
        Profile,
        Position,
        PorfileApplication,
        ProfileTag,
        ProfileNote,
        ProfileFeedback,
        PlannedEvent,
        UserCampaign,
        UserMessage,
        EventCandidateActivity,
        User,
        EmailDeliveryFeedback,
        UserCalendarEvent,
        Employee
    ]

    DB_ENTITY_TABLE_CLASS_MAP = {
        t().tablename(): t for t in DB_ENTITY_TABLE_LIST
    }

    @staticmethod
    def get_table_class(tablename):
        table_class = DBEntityTableRegistry.DB_ENTITY_TABLE_CLASS_MAP.get(tablename)
        if not table_class:
            raise UnknownTableException(f'Unknown table {tablename}. Supported tables are {list(DBEntityTableRegistry.DB_ENTITY_TABLE_LIST)}')
        return table_class

    @staticmethod
    def get_table_object(tablename):
        db_class = DBEntityTableRegistry.get_table_class(tablename)
        return db_class()


class RedshiftTableRegistry:

    ANALYTICS_TABLE_LIST = [
        UserAnalytics
    ]

    LOG_TABLE_LIST = [
        WWWServerLog
    ]

    REDSHIFT_TABLE_LIST = ANALYTICS_TABLE_LIST + LOG_TABLE_LIST
    
    REDSHIFT_TABLE_CLASS_MAP = {
        t().tablename(): t for t in REDSHIFT_TABLE_LIST
    }

    @staticmethod
    def get_table_class(tablename):
        table_class = RedshiftTableRegistry.REDSHIFT_TABLE_CLASS_MAP.get(tablename)
        if not table_class:
            raise Exception(f'Unknown table {tablename}. Supported tables are {list(RedshiftTableRegistry.REDSHIFT_TABLE_LIST)}')
        return table_class

    @staticmethod
    def get_table_object(tablename):
        db_class = RedshiftTableRegistry.get_table_class(tablename)
        return db_class()

def get_all_tablenames():
    return list(DBEntityTableRegistry.DB_ENTITY_TABLE_CLASS_MAP.keys()) + list(RedshiftTableRegistry.REDSHIFT_TABLE_CLASS_MAP.keys()) + list(DerivedTableRegistry.DERIVED_TABLE_CLASS_MAP.keys())


class DerivedTableRegistry:

    DERIVED_TABLE_LIST = [
        JtnFormSubmissionsTable,
    ]

    DERIVED_TABLE_CLASS_MAP = {
        t().tablename(): t for t in DERIVED_TABLE_LIST
    }

    @staticmethod
    def get_table_class(tablename):
        table_class = DerivedTableRegistry.DERIVED_TABLE_CLASS_MAP.get(tablename)
        if not table_class:
            raise UnknownTableException(f'Unknown derived table {tablename}. Supported tables are {list(DerivedTableRegistry.DERIVED_TABLE_CLASS_MAP.keys())}')
        return table_class

    @staticmethod
    def get_derived_table_object(tablename):
        db_class = DerivedTableRegistry.get_table_class(tablename)
        return db_class()
