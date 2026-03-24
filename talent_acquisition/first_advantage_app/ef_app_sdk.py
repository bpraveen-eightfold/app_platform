"""An SDK provided within the starter package to help app developers with certain functionality."""
import inspect
import time
import requests


class EFAppSDK:
    """Provides methods to assist various functionality for apps (within lambda function).

    This class should be defined within the specific app lambda functions and helpers,
    and should be initalized with context so as to provide the right context
    information about the lambda application to the class.
    Currently supports:
    - Logging messages to AWS CloudWatch
    - Creating Remote API Calls

    Example of how to use within Lambda Function:
    app_sdk = EFAppSDK(context)
    app_sdk.log('Example message to be logged')
    """

    def __init__(self, context):
        self.context = context

    def log(self, msg):
        """Logs messages to AWS CloudWatch.

        Takes given message and publishes in a log stream within the Cloudwatch
        group. Message will be tagged with the invocation_id of
        the current app invocation.

        Args:
            msg: A message to be logged in CloudWatch
        """
        print(f'invocation_id: {self.context.aws_request_id}, {msg}')

    def call_http_method(self, http_method, system_id=None, **kwargs):
        """Makes Remote API Call

        Calls the given HTTP request, with its specified keyword arguments, then logs
        certain details of the returned response data from the call along with metadata.

        Args:
            http_method: The HTTP method to make the request for
            system_id: The system that is calling this method
            **kwargs: The necessary keyword arguments for the HTTP request being made

        Returns:
            The response object that is returned by the HTTP request made. Calls can be made to
            the attributes of the response to get more information
        """
        start_time = time.time()
        if http_method == 'GET':
            resp = requests.get(**kwargs)       # pylint: disable=ef-requests-no-timeout
        elif http_method == 'POST':
            resp = requests.post(**kwargs)      # pylint: disable=ef-requests-no-timeout
        elif http_method == 'DELETE':
            resp = requests.delete(**kwargs)    # pylint: disable=ef-requests-no-timeout
        elif http_method == 'PATCH':
            resp = requests.patch(**kwargs)     # pylint: disable=ef-requests-no-timeout
        elif http_method == 'PUT':
            resp = requests.put(**kwargs)       # pylint: disable=ef-requests-no-timeout
        else:
            raise RuntimeError(f'Invalid http_method: {http_method}')
        end_time = time.time()

        log_data = {}
        log_data['invocation_id'] = self.context.aws_request_id
        log_data['http_method'] = http_method
        log_data['system_id'] = system_id
        log_data['caller_source'] = inspect.stack()[1][3]
        log_data.update(kwargs)
        if resp is not None:
            if not resp.ok:
                log_data['response_content'] = resp.content
            log_data['response_content_length'] = len(resp.content or '')
            log_data['response_headers'] = resp.headers if resp.headers else ''
            log_data['status_code'] = resp.status_code
        log_data['latency_milliseconds'] = int(end_time - start_time) * 1000 if resp else None

        self.log(f'remote_call_log: {log_data}')
        return resp
