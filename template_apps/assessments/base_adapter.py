import abc
import six

class BaseAdapter(six.with_metaclass(abc.ABCMeta)):
    @abc.abstractmethod
    def get_logo_url(self):
        pass

    @abc.abstractmethod
    def is_webhook_supported(self):
        pass

    @abc.abstractmethod
    def list_tests(self, request_data):
        pass

    @abc.abstractmethod
    def invite_candidate(self, request_data):
        pass

    @abc.abstractmethod
    def fetch_candidate_report(self, request_data):
        pass
