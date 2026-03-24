from __future__ import absolute_import

from enum import Enum


class TeamsNotificationTypes(Enum):
    def __new__(cls, value, file_path):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.file_path = file_path
        return obj

    FEEDBACK_REQUESTED = ('feedback_requested', 'templates/feedback_requested.txt')
    FEEDBACK_SUBMITTED = ('feedback_submitted', 'templates/feedback_submitted.txt')
    FEEDBACK_REMINDER = ('feedback_reminder', 'templates/feedback_reminder.txt')
    FEEDBACK_CANCELLED = ('feedback_cancelled', 'templates/feedback_cancelled.txt')

    @classmethod
    def values(cls):
        return list(cls)

    @classmethod
    def from_value(cls, value):
        return next(iter(filter(lambda element: element._value_ == value, list(cls))), None)
