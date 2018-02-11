import argparse
import cmd2
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

class ClanvasCmd(cmd2.Cmd):

    debug = True

    prompt = property(lambda self: self.clanvas.get_prompt())

    def __init__(self):
        super(ClanvasCmd, self).__init__()
        self.clanvas = None

    def do_login(self, line):
        if self.clanvas is not None:
            print('Already logged in.')
            return False

        items = line.split()
        if not len(items) == 2:
            print('Please provide a URL and a valid token.')
            return False

        url = items[0]
        token = items[1]

        self.clanvas = Clanvas(url, token)
        self.clanvas.login_info()

    def do_whoami(self, line):
        self.clanvas.whoami(line == '-v')

    lc_parser = argparse.ArgumentParser()
    lc_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
    lc_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    lc_parser.add_argument('-i', '--invalidate', action='store_true', help='invalidate cached course info')

    @cmd2.with_argparser(lc_parser)
    def do_lc(self, opts):
        self.clanvas.list_courses(all=opts.all, long=opts.long, invalidate=opts.invalidate)

    def do_cc(self, course_string):
        if course_string == '':
            print('Please specify a course (try lc).')
            return False

        courses = self.clanvas.get_courses()
        match_courses = [course for course in courses if course.id == int(course_string)]

        if len(match_courses) > 1:
            print('Ambiguous course info, matched multiple courses.')
        elif len(match_courses) < 1:
            print('Could not find a matching course')
        else:
            self.clanvas.change_course(match_courses[0].id)

        return False

    def complete_cc(self, text, line, begidx, endidx):
        query = line[3:].replace(' ', '').lower()
        courses = self.clanvas.get_courses()

        digest_cache = {}

        # get a searchable string with all the data we want for autocomplete options
        def queryable_digest(course):
            nonlocal digest_cache
            if course.id not in digest_cache:
                digest_cache[course.id] = ''.join([str(item) for item in Clanvas.list_long_row(course)]).replace(' ', '').lower()
            return digest_cache[course.id]

        return [str(course.id) for course in courses if query in queryable_digest(course)]

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