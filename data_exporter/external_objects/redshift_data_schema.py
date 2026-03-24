from marshmallow import Schema
from marshmallow import fields

from utils import str_utils
from utils import time_utils

class UserAnalyticsSchema(Schema):

    event = fields.String(attribute='event')
    userId = fields.String(attribute='user_id')
    positionId = fields.String(attribute='position_id')
    source = fields.String(attribute='source')
    createAt = fields.Method('get_unix_timestamp')
    num = fields.Integer(attribute='num')
    profileId = fields.String(attribute='profile_id')

    def get_unix_timestamp(self, user_analytics_dict):
        timestamp = user_analytics_dict.get('timestamp')
        return str_utils.safe_get_int(time_utils.to_timestamp(timestamp, default=None))


class WWWServerLogSchema(Schema):

    id = fields.String(attribute='unique_id')
    namespace = fields.String(attribute='namespace')
    event = fields.String(attribute='event')
    userEmail = fields.String(attribute='user_email')
    userCompany = fields.String(attribute='user_company')
    createAt = fields.String(attribute='t_create')
    requestEndpoint = fields.String(attribute='request_endpoint')
    latencyMilliseconds = fields.Integer(attribute='latency_milliseconds')
    referrer = fields.String(attribute='referrer')
    responseCode = fields.String(attribute='response_code')
    userAgent = fields.String(attribute='user_agent')
    hostname = fields.String(attribute='hostname')
    requestPath = fields.String(attribute='request_path')
    referrerPath = fields.String(attribute='referrer_path')
    requestMethod = fields.String(attribute='request_method')
    redirectUrl = fields.String(attribute='redirect_url')
    vsCookie = fields.String(attribute='vs_cookie')
    query = fields.String(attribute='query')
    interface = fields.String(attribute='interface')
    country = fields.String(attribute='country')
    positionId = fields.String(attribute='position_id')
    utmSource = fields.String(attribute='utm_source')
    utmCampaign = fields.String(attribute='utm_campaign')
