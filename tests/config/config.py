import unittest
from os.path import join, dirname, abspath

from clanvas.config import parse_clanvas_config_file


def parse(filename):
    return parse_clanvas_config_file(join(dirname(abspath(__file__)), filename))


expected_1 = {}
expected_2 = {"site1": {"url": "canvas.website1.edu", "token": "1234~ZDUtxyIhxCOYNwDd1Szk8KRy6YZ31jZduvmozrfmDhQe3bLfDTx7AnwPOqofxmfU"}}
expected_3 = {"site1": {"url": "canvas.website1.edu", "token": "1234~ZDUtxyIhxCOYNwDd1Szk8KRy6YZ31jZduvmozrfmDhQe3bLfDTx7AnwPOqofxmfU"}, "site2": {"url": "canvas.website2.edu", "token": "apW5q2kxoi9o6tUXM7gNKhvtOLMPrS49jZNbp7g9JRoMuKkKdhDLTRPD3sluDIzx"}}


class TestConfigParser(unittest.TestCase):

    def test_1(self):
        self.assertDictEqual(expected_1, parse('config_1'))

    def test_2(self):
        self.assertDictEqual(expected_2, parse('config_2'))

    def test_3(self):
        self.assertDictEqual(expected_3, parse('config_3'))


# if __name__ == '__main__':
#     import json
#     print(json.dumps(parse('config_2')))


