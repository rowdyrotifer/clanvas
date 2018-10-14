import os
import os
import unittest
from argparse import ArgumentParser
from functools import reduce
from os import listdir
from os.path import isfile, join, dirname, abspath, expanduser

import requests_mock

from clanvas.clanvas import Clanvas
from tests.register import register_uris

login_command = 'login https://example.com 123'

login_requirements = {'user': {'self', 'profile'}, 'courses': {'courses'}}

script_requirements = {
    'whoami': {
        'whoami': login_requirements,
        'whoami_verbose': login_requirements
    },
    'lc': {
        'lc': login_requirements,
        'lc_long': login_requirements,
        'lc_all': login_requirements,
        'lc_long_all': login_requirements
    }
}


class TestRegression(unittest.TestCase):
    def run_all_regression_tests(self):
        for command_name, script_names in script_requirements.items():
            for script_name in script_names.keys():
                with self.subTest():
                    test_transcript(command_name, script_name)


def compose_requirements(*args):
    def merge_dicts(d1, d2):
        keys = set(d1).union(d2)
        return dict((k, d1.get(k, set()) + d2.get(k, set())) for k in keys)
    return reduce(merge_dicts, args)


def generate_transcript(command_name, script_name):
    regression_action(command_name, script_name, _generate_transcript)


def _generate_transcript(clanvas_file, output_file):
    clanvas = Clanvas()
    clanvas.onecmd(login_command)

    with open(clanvas_file, 'r') as f:
        for line in f.readlines():
            clanvas.onecmd(line)

    clanvas.onecmd(f'history 2: -t "{output_file}"')


def test_transcript(command_name, script_name):
    regression_action(command_name, script_name, _test_transcript)


def _test_transcript(_, output_file):
    clanvas = Clanvas(transcript_files=[output_file])
    clanvas.onecmd(login_command)
    clanvas.cmdloop()  # runs the regression test automagically from the transcript


def regression_action(command_name, script_name, action):
    if command_name not in script_requirements or script_name not in script_requirements[command_name]:
        raise ValueError(f'Script requirements for {script_name} not specified in regression.py')

    with requests_mock.Mocker() as m:
        register_uris(script_requirements[command_name][script_name], m)

        clanvas_file = join(dirname(abspath(__file__)), command_name, script_name)
        output_file = join(dirname(abspath(__file__)), command_name, script_name + '.out')
        prev = os.getcwd()
        os.chdir(expanduser('~'))
        action(clanvas_file, output_file)
        os.chdir(prev)


if __name__ == '__main__':
    regression_dir = os.path.dirname(__file__)
    command_dirs = [os.path.join(regression_dir, d) for d in listdir(regression_dir) if not isfile(join(regression_dir, d))]
    command_scripts = [os.path.join(d, f) for d in command_dirs for f in listdir(d) if '.' not in f]

    parser = ArgumentParser(description='Generate transcripts for regression tests.')
    parser.add_argument('commands', nargs='+', help='Name of commands to regenerate tests for.')
    args = parser.parse_args()

    for command_name in args.commands:
        if command_name in script_requirements:
            for script_name in script_requirements[command_name]:
                print(f'Generating transcript for {command_name}/{script_name}')
                generate_transcript(command_name, script_name)
        else:
            print(f'No scripts found for command {command_name}')
