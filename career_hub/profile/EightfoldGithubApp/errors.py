import json

from constants import GITHUB_LOGO_URL


class RequestValidationError(Exception):
    def __init__(self, message='', status_code=None):
        super(RequestValidationError, self).__init__()
        self.message = message
        self.status_code = status_code

    def to_error_response(self):
        return {
            'statusCode': self.status_code,
            'body': json.dumps({'error': self.message}),
        }

class GitHubUsernameError(Exception):

    def __init__(self, message='', status_code=None):
        super(GitHubUsernameError, self).__init__()
        self.message = message
        self.status_code = status_code

    def to_error_response(self):
        data = {
            'title': 'Github',
            'logo_url': GITHUB_LOGO_URL,
            'error': self.message
        }
        return {
            'statusCode': 200,
            'body': json.dumps({'data': data, 'cache_ttl_seconds': 1800})
        }
