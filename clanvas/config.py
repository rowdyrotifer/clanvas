import json
from itertools import groupby


class InvalidConfigurationException(Exception):
    message: str

    def __init__(self, message):
        self.message = message


VALID_KEYS = {'default', 'url', 'token'}


def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


def parse_group(group_items):
    name = group_items[0]
    mappings = {k.lower(): v for k, v in pairwise(group_items[1:])}

    # Check for invalid configuration keys
    invalid_key = next((key for key in mappings.keys() if key not in VALID_KEYS), None)
    if invalid_key:
        raise InvalidConfigurationException(f'Key "{invalid_key}" is not valid, '
                                            f'should be one of: {", ".join(VALID_KEYS)}')

    return name, mappings


def parse_clanvas_config_structure(config_string):
    tokens = config_string.split()
    groups = [list(g) for k, g in groupby(tokens, lambda x: x.lower() != 'host') if k]
    return dict(map(parse_group, groups))


def parse_clanvas_config(config_string):
    entries = parse_clanvas_config_structure(config_string)

    default_name = next((name for name, mappings in entries.items()
                         if 'default' in mappings and mappings['default'].lower() == 'true'), None)

    if default_name:
        del entries[default_name]['default']
        return {'default': default_name,
                'entries': entries}
    else:
        return {'entries': entries}


if __name__ == "__main__":
    import os
    with open(os.path.expanduser('~/clanvasconfig'), 'r') as f:
        results = parse_clanvas_config(f.read())
        print(json.dumps(results))
