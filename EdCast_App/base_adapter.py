import abc
import six

class BaseAdapter(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_current_courses(self, req_data):
        pass

    @abc.abstractmethod
    def get_recommended_courses(self, req_data):
        pass
