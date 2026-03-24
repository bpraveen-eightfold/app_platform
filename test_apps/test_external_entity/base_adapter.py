import abc
import six

class BaseAdapter(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_current_courses(self, req_data, app_settings):
        pass

    @abc.abstractmethod
    def get_courses_search_results(self, req_data, app_settings):
        pass

    @abc.abstractmethod
    def get_course_details(self, req_data):
        pass
