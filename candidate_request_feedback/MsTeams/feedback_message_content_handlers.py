from __future__ import absolute_import

from teams_message_content_handler import MSTeamsMessageContentHandler
from teams_notification_types import TeamsNotificationTypes

class FeedbackRequestContentHandler(MSTeamsMessageContentHandler):
    def get_notification_type(self):
        return TeamsNotificationTypes.FEEDBACK_REQUESTED


class FeedbackSubmitContentHandler(MSTeamsMessageContentHandler):
    def get_notification_type(self):
        return TeamsNotificationTypes.FEEDBACK_SUBMITTED


class FeedbackReminderContentHandler(MSTeamsMessageContentHandler):
    def get_notification_type(self):
        return TeamsNotificationTypes.FEEDBACK_REMINDER


class FeedbackCancelContentHandler(MSTeamsMessageContentHandler):
    def get_notification_type(self):
        return TeamsNotificationTypes.FEEDBACK_CANCELLED
