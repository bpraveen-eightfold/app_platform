AWS_DEFAULT_REGION = 'us-west-2'

def get_region_domain(region=None):
    region = region or AWS_DEFAULT_REGION
    region_prefix_map = {
        'us-west-2': 'eightfold',
        'eu-central-1': 'eightfold-eu',
        'us-gov-west-1': 'eightfold-gov',
        'ca-central-1': 'eightfold-ca',
        'me-central-1': 'eightfold-me'
    }
    return region_prefix_map[region]
