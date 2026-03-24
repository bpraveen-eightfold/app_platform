from abc import ABC, abstractmethod

API_CHANGELOG_ENDPOINT = 'api/v2/core/changelog'
BATCH_FETCH_ENDPOINT = 'api/v2/{namespace}/{entity_name}/batch-fetch'
DEFAULT_NUM_FETCH_PER_REQ = 100

class DBEntityTable(ABC):
    
    @abstractmethod
    def tablename(self):
        '''
        Customer facing table name (External tablename). Not EF internal tablename
        '''
        pass

    def __str__(self):
        return self.tablename()

    def namespace(self):
        return 'core'

    def api_server_entity_name(self):
        return self.tablename().replace('_', '-')

    def id_col(self):
        return 'id'

    def changelog_endpoint_entity_name(self):
        return self.api_server_entity_name()

    def change_log_endpoint(self):
        return f'{API_CHANGELOG_ENDPOINT}/{self.tablename()}'

    def batch_get_entity_endpoint(self):
        return BATCH_FETCH_ENDPOINT.format(namespace=self.namespace(), entity_name=self.tablename())

    def fields_to_exclude(self):
        return []

    def fields_to_include(self):
        return []

    def batch_fetch_size_per_req(self):
        return DEFAULT_NUM_FETCH_PER_REQ

class Profile(DBEntityTable):

    def tablename(self):
        return 'profiles'

    def changelog_endpoint_entity_name(self):
        return 'profile'

    def fields_to_exclude(self):
        return ['tags', 'notes', 'resume', 'applications','inferredSkills', 'attachmentsInfo']

    def fields_to_include(self):
        return ['deletedAt', 'careerSiteQuestions']

class Position(DBEntityTable):

    def tablename(self):
        return 'positions'

    def id_col(self):
        return 'positionId'

    def changelog_endpoint_entity_name(self):
        return 'position'

    def fields_to_exclude(self):
        return ['role', 'atsData', 'calibrationData', 'groupId']

class PorfileApplication(DBEntityTable):

    def tablename(self):
        return 'profile-applications'

    def fields_to_exclude(self):
        return ['candidateProfile', 'position', 'feedback', 'positionTitle', 'groupId']

class ProfileTag(DBEntityTable):

    def tablename(self):
        return 'profile-tags'

class ProfileNote(DBEntityTable):

    def tablename(self):
        return 'profile-notes'

class ProfileFeedback(DBEntityTable):

    def tablename(self):
        return 'profile-feedbacks'

    def changelog_endpoint_entity_name(self):
        return 'profile-feedback'

    def id_col(self):
        return 'feedbackId'

    def fields_to_exclude(self):
        return ['matchingData', 'position']

class PlannedEvent(DBEntityTable):

    def tablename(self):
        return 'planned-events'

    def namespace(self):
        return 'events'

    def changelog_endpoint_entity_name(self):
        return 'planned-event'

class UserCampaign(DBEntityTable):

    def tablename(self):
        return 'user-campaigns'

class UserMessage(DBEntityTable):

    def tablename(self):
        return 'user-messages'

    def fields_to_exclude(self):
        return ['matchingData', 'emailContent']

class EventCandidateActivity(DBEntityTable):

    def tablename(self):
        return 'event-candidate-activities'

    def namespace(self):
        return 'events'

class User(DBEntityTable):

    def tablename(self):
        return 'users'

    def changelog_endpoint_entity_name(self):
        return 'user-login'

    def fields_to_exclude(self):
        return ['atsData']

    def fields_to_include(self):
        return ['lastLoginTimeStamp']

    def batch_fetch_size_per_req(self):
        return 20 # This table is a little slower compared to other tables

class EmailDeliveryFeedback(DBEntityTable):

    def tablename(self):
        return 'email-delivery-feedbacks'

class UserCalendarEvent(DBEntityTable):

    def tablename(self):
        return 'user-calendar-events'

class Employee(DBEntityTable):

    def tablename(self):
        return 'employees'

    def fields_to_exclude(self):
        return []

    def fields_to_include(self):
        return []

    def change_log_endpoint(self):
        # We use ID from profile for this case
        return f'{API_CHANGELOG_ENDPOINT}/profiles'
