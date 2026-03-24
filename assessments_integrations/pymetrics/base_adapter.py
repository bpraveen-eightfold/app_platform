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
	def list_tests(self):
		pass

	@abc.abstractmethod
	def invite_candidate(self):
		pass

	@abc.abstractmethod
	def fetch_reports(self):
		pass

	@abc.abstractmethod
	def fetch_candidate_report(self):
		pass
