"""Canonical respresentation of Availability entities"""
from __future__ import absolute_import


class AvailabilityOAuthCredentials:
    """ Holder for availability OAuth Credentials """
    def __init__(self):
        self.url = None
        self.client_id = None
        self.client_secret = None
        self.resource_id = None
        self.grant_type = None


class AvailabilityCredentials:
    """ Holder for availability Credentials """
    def __init__(self):
        self.api_url = None
        self.oauth = None
