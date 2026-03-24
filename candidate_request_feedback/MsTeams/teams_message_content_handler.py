from __future__ import absolute_import

import abc
import copy
from jinja2 import Environment, FileSystemLoader
import six
from teams_notification_types import TeamsNotificationTypes

class MSTeamsMessageContentHandler(six.with_metaclass(abc.ABCMeta)):
    def __init__(self, request_data, app_settings, trigger_name):
        self.request_data = request_data or {}
        self.app_settings = app_settings or {}
        self.trigger_name = trigger_name
    
    def get_message_content(self):
        template_file_content = open(self.get_template_file()).read()
        jinja_template_obj = Environment(loader=FileSystemLoader('.')).get_template(self.get_template_file())
        return jinja_template_obj.render(self.get_var_map()).replace('\n', '')

    @abc.abstractmethod
    def get_notification_type():
        pass

    def get_template_file(self):
        return TeamsNotificationTypes.from_value(self.get_notification_type()._value_).file_path

    def get_var_map(self):
        var_map = copy.deepcopy(self.request_data)
        var_map.update(copy.deepcopy(self.app_settings))
        return var_map
