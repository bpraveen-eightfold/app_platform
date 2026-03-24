from collections import namedtuple

REDSHIFT_ANALYTICS_IDENTIFIER = 'analytics'
REDSHIFT_LOG_INDENTIFIER = 'log'
REDSHIFT_ANALYTICS_CONSUMER_INDENTIFIER = 'analytics-consumer'
APP_PLATFORM_ECS_PROXY_IP = '172.15.23.137'

RedshiftMetadata = namedtuple('RedshiftMetadata', 'host cluster_identifier')

PROXY_PORT_MAPPING = {
    'us-west-2': 5439,
    'eu-central-1': 5440,
    'ca-central-1': 5441,
    'us-gov-west-1': 5442,
    'me-central-1': 5443
}

REDSHIFT_CLUSTER_URL = {
    'us-west-2': 'analytics-consumer.cakmd01d4jtp.us-west-2.redshift.amazonaws.com',
    'eu-central-1': 'analytics-consumer.cieqgsdspopu.eu-central-1.redshift.amazonaws.com',
    'ca-central-1': 'analytics-consumer.casklpn7vawb.ca-central-1.redshift.amazonaws.com',
    'us-gov-west-1': 'analytics-consumer.cq7wkcwhcqsx.us-gov-west-1.redshift.amazonaws.com'
}


def get_datawarehouse_host(region):
    # TODO - Use the following mapping instead of Static IP whenever we modified AppPlatform Proxy to use NAT for a static IP
    # This APP_PLATFORM_ECS_PROXY_IP is a solution for static IP for AppPlatform ECS App 
    # region_domain = url_utils.get_region_domain(region)
    # return f'datawarehouse.{region_domain}.ai'
    redshift_host = REDSHIFT_CLUSTER_URL.get(region)
    if not redshift_host:
        raise Exception(f'Unknown region: {region}')
    return redshift_host

def get_cluster_metadata_map(region=None):
    dw_host = get_datawarehouse_host(region)
    return {
        'analytics': RedshiftMetadata(dw_host, REDSHIFT_ANALYTICS_CONSUMER_INDENTIFIER)
    }
