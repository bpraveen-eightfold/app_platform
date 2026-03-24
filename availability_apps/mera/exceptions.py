import json


class AvailabilityAppException(Exception):
    def __init__(self, message='', status_code=None):
        super().__init__()
        self.message = message
        self.status_code = status_code

    def to_error_response(self):
        return {
            'statusCode': self.status_code,
            'body': json.dumps({'error': self.message}),
        }
