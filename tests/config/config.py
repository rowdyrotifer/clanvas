import unittest
from os.path import join, dirname, abspath

from clanvas.config import parse_clanvas_config


def parse(filename):
    with open(join(dirname(abspath(__file__)), filename), 'r') as f:
        config_string = f.read()
        return parse_clanvas_config(config_string)


expected_0 = {"entries": {}}
expected_1 = {"entries": {"site1": {"url": "canvas.website1.edu", "token": "1234~ZDUtxyIhxCOYNwDd1Szk8KRy6YZ31jZduvmozrfmDhQe3bLfDTx7AnwPOqofxmfU"}}}
expected_2 = {"default": "site1", "entries": {"site1": {"url": "canvas.website1.edu", "token": "1234~ZDUtxyIhxCOYNwDd1Szk8KRy6YZ31jZduvmozrfmDhQe3bLfDTx7AnwPOqofxmfU"}}}
expected_3 = {"default": "site1", "entries": {"site1": {"url": "canvas.website1.edu", "token": "1234~ZDUtxyIhxCOYNwDd1Szk8KRy6YZ31jZduvmozrfmDhQe3bLfDTx7AnwPOqofxmfU"}, "site2": {"url": "canvas.website2.edu", "token": "apW5q2kxoi9o6tUXM7gNKhvtOLMPrS49jZNbp7g9JRoMuKkKdhDLTRPD3sluDIzx"}}}


class TestConfigParser(unittest.TestCase):
    def test_0(self):
        self.assertDictEqual(expected_0, parse('config_0'))

    def test_1(self):
        self.assertDictEqual(expected_1, parse('config_1'))

    def test_2(self):
        self.assertDictEqual(expected_2, parse('config_2'))

    def test_3(self):
        self.assertDictEqual(expected_3, parse('config_3'))


# if __name__ == '__main__':
#     import json
#     print(json.dumps(parse('config_1')))


