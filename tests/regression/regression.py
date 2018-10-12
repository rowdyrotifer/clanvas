import os
import unittest
from functools import reduce

import requests_mock

from clanvas.clanvas import Clanvas
from tests.register import register_uris

login_command = 'login https://example.com 123'

login_requirements = {'user': {'self', 'profile'}, 'courses': {'courses'}}

script_requirements = {
    'whoami/whoami': login_requirements,
    'whoami/whoami_verbose': login_requirements
}


class TestRegression(unittest.TestCase):
    def run_all_regression_tests(self):
        for script in script_requirements.keys():
            with self.subTest():
                regression_transcript_test(script)


def compose_requirements(*args):
    def merge_dicts(d1, d2):
        keys = set(d1).union(d2)
        return dict((k, d1.get(k, set()) + d2.get(k, set())) for k in keys)
    return reduce(merge_dicts, args)


def generate_transcript(script):
    if script not in script_requirements:
        raise ValueError('Script requirements not specified in regression.py')
    requirements = script_requirements[script]
    os.chdir(os.path.expanduser('~'))
    with requests_mock.Mocker() as m:
        register_uris(requirements, m)

        regression_dir = os.path.dirname(__file__)
        clanvas_file = os.path.join(regression_dir, script)
        output_file = os.path.join(regression_dir, script) + '.out'

        clanvas = Clanvas()
        clanvas.onecmd(login_command)

        with open(clanvas_file, 'r') as f:
            for line in f.readlines():
                clanvas.onecmd(line)

        clanvas.onecmd(f'history 2: -t "{output_file}"')


def regression_transcript_test(script):
    if script not in script_requirements:
        raise ValueError('Script requirements not specified in regression.py')
    requirements = script_requirements[script]
    os.chdir(os.path.expanduser('~'))
    with requests_mock.Mocker() as m:
        register_uris(requirements, m)

        regression_dir = os.path.dirname(__file__)
        transcript_file = f'{os.path.join(regression_dir, script)}.out'

        clanvas = Clanvas(transcript_files=[transcript_file])
        clanvas.onecmd(login_command)
        clanvas.cmdloop()  # runs the regression test automagically from the transcript
