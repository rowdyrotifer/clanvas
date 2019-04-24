from itertools import groupby
from urllib.parse import urlparse


class InvalidClanvasConfigurationException(Exception):
    message: str

    def __init__(self, message):
        self.message = message


VALID_KEYS = {'default', 'url', 'token'}

REQUIRED_KEYS = {'url', 'token'}


def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


def parse_group(group_items):
    name = group_items[0]
    mappings = {k.lower(): v for k, v in pairwise(group_items[1:])}

    # Check for invalid configuration keys
    invalid_key = next((key for key in mappings.keys() if key not in VALID_KEYS), None)
    if invalid_key:
        raise InvalidClanvasConfigurationException(f'Host "{name}" has invalid key "{invalid_key}". '
                                                   f'Should be one of: {", ".join(VALID_KEYS)}.')

    # Check for missing required keys
    required_key = next((key for key in REQUIRED_KEYS if key not in mappings.keys()), None)
    if required_key:
        raise InvalidClanvasConfigurationException(f'Host "{name}" missing required key "{required_key}".')

    # Ensure URL is valid
    url_components = urlparse(mappings['url'])
    if url_components.scheme == '':
        raise InvalidClanvasConfigurationException(f'Host "{name}" has invalid URL. No URL scheme provided.')

    return name, mappings


def parse_clanvas_config_file(filename):
    with open(filename, 'r') as f:
        config_string = f.read()
        return parse_clanvas_config(config_string)


def parse_clanvas_config(config_string):
    tokens = config_string.split()
    groups = [list(g) for k, g in groupby(tokens, lambda x: x.lower() != 'host') if k]
    return dict(map(parse_group, groups))


# if __name__ == "__main__":
#     import os
#     with open(os.path.expanduser('~/clanvasconfig'), 'r') as f:
#         results = parse_clanvas_config(f.read())
#         print(json.dumps(results))
