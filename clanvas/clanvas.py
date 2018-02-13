import argparse
import os
from os.path import isfile, join
from urllib.parse import urlparse

import cmd2
import colorama
from canvasapi import Canvas
from canvasapi.course import Course
from colorama import Fore, Style
from tabulate import tabulate
from tzlocal import get_localzone

local_tz = get_localzone()

# Extend the course object to have a readable-yet-unique code that is course code + id
Course.unique_course_code = property(lambda self: self.course_code.replace(' ', '') + '-' + str(self.id))

class Clanvas(cmd2.Cmd):

    def __init__(self):
        super(Clanvas, self).__init__()

        self.url = None
        self.host = None
        self.canvas = None  # type: Canvas

        self.home = os.path.expanduser("~")

        self.current_course = None  # type: Course
        self.current_directory = self.home

        self.__courses = None
        self.__courses_digest_cache = {}
        self.__current_user_profile = None

    def get_courses(self, invalidate=False):
        if self.__courses is None or invalidate:
            sorter = lambda course: (-course.enrollment_term_id, course.name)
            self.__courses = sorted(self.canvas.get_current_user().get_courses(), key=sorter)

        return self.__courses

    def current_user_profile(self, invalidate=False):
        if self.__current_user_profile is None or invalidate:
            self.__current_user_profile = self.canvas.get_current_user().get_profile()

        return self.__current_user_profile

    @staticmethod
    def course_info_items(c):
        return [c.course_code, c.id, c.start_at_date.strftime("%b %y") if hasattr(c, 'start_at_date') else '', c.name]

    @staticmethod
    def course_query_items(c):
        return [c.course_code, c.id, c.unique_course_code, c.name]

    @staticmethod
    def assignment_info_items(a):
        return [a.id, a.due_at_date.astimezone(local_tz).strftime("%a, %d %b %I:%M%p") if hasattr(a, 'due_at_date') else '', a.name]

    @staticmethod
    def query_courses(courses, query):
        return filter(lambda course: any([query in str(item) for item in Clanvas.course_query_items(course)]), courses)

    # cmd2 attribute, made dynamic with get_prompt()
    prompt = property(lambda self: self.get_prompt())

    prompt_string = Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':' + Fore.MAGENTA + '{pwc}' + Style.RESET_ALL + ':' + Fore.CYAN + '{pwd} ' + Style.RESET_ALL + '$ '

    def get_prompt(self):
        if self.canvas is None:
            return '$ '

        login_id = self.current_user_profile()['login_id']
        host = self.host
        pwc = self.current_course.course_code if self.current_course is not None else '~'
        pwd = self.current_directory.replace(self.home, '~')

        return self.prompt_string.format(
            login_id=login_id,
            host=host,
            pwc=pwc,
            pwd=pwd
        )

    #     _____                                          _
    #    / ____|                                        | |
    #   | |     ___  _ __ ___  _ __ ___   __ _ _ __   __| |___
    #   | |    / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
    #   | |___| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
    #    \_____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/
    #

    la_parser = argparse.ArgumentParser()
    la_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
    la_parser.add_argument('-l', '--long', action='store_true', help='long listing')

    @cmd2.with_argparser(la_parser)
    def do_la(self, opts):
        if self.current_course is None:
            print('Please select a course')
            return False

        display_assignments = self.current_course.get_assignments()

        if opts.long:
            print(tabulate(map(Clanvas.assignment_info_items, display_assignments), tablefmt='plain'))
        else:
            print('\n'.join([assignment.name for assignment in display_assignments]))

    login_parser = argparse.ArgumentParser()
    login_parser.add_argument('url', help='URL of Canvas server')
    login_parser.add_argument('token', help='Canvas API access token')

    @cmd2.with_argparser(login_parser)
    def do_login(self, opts):
        if self.canvas is not None:
            print('Already logged in.')
            return False

        self.url = opts.url
        self.host = urlparse(opts.url).netloc

        self.canvas = Canvas(opts.url, opts.token)

        profile = self.current_user_profile()
        print('Logged in as {:s} ({:s})'.format(profile['name'], profile['login_id']))

    def do_ls(self, line):
        pass

    lc_parser = argparse.ArgumentParser()
    lc_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
    lc_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    lc_parser.add_argument('-i', '--invalidate', action='store_true', help='invalidate cached course info')

    @cmd2.with_argparser(lc_parser)
    def do_lc(self, opts):
        courses = self.get_courses(opts.invalidate)

        if opts.all:
            display_courses = courses
        else:
            latest_term = max(course.enrollment_term_id for course in courses)
            display_courses = filter(lambda course: course.enrollment_term_id == latest_term, courses)

        if opts.long:
            print(tabulate(map(Clanvas.course_info_items, display_courses), tablefmt='plain'))
        else:
            print('\n'.join([course.course_code for course in display_courses]))

    cc_parser = argparse.ArgumentParser()
    cc_parser.add_argument('course', nargs='?', default='', help='course id or matching course string (e.g. the course code)')

    @cmd2.with_argparser(cc_parser)
    def do_cc(self, opts):
        if opts.course is '' or opts.course is '~':
            self.current_course = None
            return False

        courses = self.get_courses()
        matched_courses = list(Clanvas.query_courses(courses, opts.course))
        num_matches = len(matched_courses)

        if num_matches == 1:
            self.current_course = matched_courses[0]
        elif num_matches > 1:
            print('Ambiguous input "{:s}".'.format(opts.course))
            print('Please select an option:')

            pad_length = len(str(num_matches)) + 2
            format_str = '{:<' + str(pad_length) + '}{}'

            print(format_str.format('0)', 'cancel'))
            count = 1
            for course in matched_courses:
                print(format_str.format(f'{count})', course.unique_course_code))
                count += 1

            choice = input('Enter number: ')
            if choice.isdigit():
                num_choice = int(choice)
                if num_choice > num_matches:
                    print(f'Choice {num_choice} greater than last choice ({num_matches}).')
                elif num_choice != 0:
                    self.current_course = matched_courses[num_choice - 1]
            else:
                print(f'Choice {choice} is not numeric.')
        else:
            print('Could not find a matching course.')

        return False

    def complete_cc(self, text, line, begidx, endidx):
        query = line[3:].replace(' ', '').lower()
        courses = self.get_courses()

        return [course.unique_course_code for course in Clanvas.query_courses(courses, query)]

    whoami_parser = argparse.ArgumentParser()
    whoami_parser.add_argument('-v', '--verbose', action='store_true', help='display more info about the logged in user')

    @cmd2.with_argparser(whoami_parser)
    def do_whoami(self, opts):
        profile = self.canvas.get_current_user().get_profile()

        if not opts.verbose:
            print(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            print('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))


rc_file = join(os.path.expanduser('~'), '.clanvasrc')

if __name__ == '__main__':
    colorama.init()  # Windows color support

    cmd = Clanvas()
    if isfile(rc_file):
        cmd.onecmd('load ' + rc_file)
    cmd.cmdloop()
