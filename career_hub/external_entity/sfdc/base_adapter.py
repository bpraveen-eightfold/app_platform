import abc
import six

class BaseAdapter(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_entity_search_results(self, req_data):
        pass

    @abc.abstractmethod
    def get_entity_details(self, req_data):
        pass
