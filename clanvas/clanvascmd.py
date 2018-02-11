import cmd
import configparser

import os

from os.path import isfile

import sys
from pip.utils import appdirs

from clanvas import Clanvas


def clanvas_config_dir():
    return appdirs.user_config_dir('clanvas', 'clanvas')

def clanvas_config_file():
    return os.path.join(clanvas_config_dir(), 'clanvas.conf')

def clanvas_data_dir():
    return appdirs.user_data_dir('clanvas', 'clanvas')

def clanvas_config() -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        config.read(clanvas_config_file())
        return config

class ClanvasCmd(cmd.Cmd):

    prompt = 'clanvas> '

    def __init__(self):
        super(ClanvasCmd, self).__init__()
        self.clanvas = None

    def do_login(self, line):
        if self.clanvas is not None:
            print('Already logged in.')
            return False

        items = line.split()
        if not len(items) == 2:
            return 'Please provide a URL and a valid token.'

        url = items[0]
        token = items[1]

        self.clanvas = Clanvas(url, token)
        self.clanvas.welcome()

    def do_whoami(self, line):
        self.clanvas.whoami(line == 'verbose')

    def do_ls(self, line):
        pass

    def do_EOF(self, line):
        return True


if __name__ == '__main__':
    if not isfile(clanvas_config_file()):
        print('Please create ' + clanvas_config_file())
        sys.exit(0)

    config = clanvas_config()
    url = config.get('Clanvas', 'url')
    token = config.get('Clanvas', 'token')

    cmd = ClanvasCmd()
    cmd.onecmd('login ' + url + ' ' + token)
    cmd.cmdloop()