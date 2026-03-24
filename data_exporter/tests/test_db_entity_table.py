import unittest

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

class TestDBEntityTable(unittest.TestCase):

    def test_changelog_endpoint_entity_name(self):
        self.assertEqual(Profile().change_log_endpoint(), 'api/v2/core/changelog/profile')
        self.assertEqual(Position().change_log_endpoint(), 'api/v2/core/changelog/position')
        self.assertEqual(PorfileApplication().change_log_endpoint(), 'api/v2/core/changelog/profile-applications')
        self.assertEqual(ProfileTag().change_log_endpoint(), 'api/v2/core/changelog/profile-tags')
        self.assertEqual(ProfileNote().change_log_endpoint(), 'api/v2/core/changelog/profile-notes')
        self.assertEqual(ProfileFeedback().change_log_endpoint(), 'api/v2/core/changelog/profile-feedback')
        self.assertEqual(PlannedEvent().change_log_endpoint(), 'api/v2/core/changelog/planned-event')
        self.assertEqual(UserCampaign().change_log_endpoint(), 'api/v2/core/changelog/user-campaigns')
        self.assertEqual(UserMessage().change_log_endpoint(), 'api/v2/core/changelog/user-messages')
        self.assertEqual(EventCandidateActivity().change_log_endpoint(), 'api/v2/core/changelog/event-candidate-activity')
        self.assertEqual(User().change_log_endpoint(), 'api/v2/core/changelog/user-login')
        self.assertEqual(EmailDeliveryFeedback().change_log_endpoint(), 'api/v2/core/changelog/email-delivery-feedbacks')
        self.assertEqual(UserCalendarEvent().change_log_endpoint(), 'api/v2/core/changelog/user-calendar-events')
