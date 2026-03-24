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
	def list_tests(self, req_data):
		pass

	@abc.abstractmethod
	def invite_candidate(self, req_data):
		pass

	@abc.abstractmethod
	def fetch_reports(self, req_data):
		pass

	@abc.abstractmethod
	def fetch_candidate_report(self, req_data):
		pass

	@abc.abstractmethod
	def process_webhook_request(self, req_data):
		pass
