from __future__ import absolute_import

import xmltodict

def convert_to_dict(xml_payload):
    return xmltodict.parse(xml_payload)
