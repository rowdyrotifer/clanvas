import argparse
import functools
import os
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from os.path import isfile, join
from urllib.parse import urlparse

import cmd2
import colorama
import pytz
from canvasapi import Canvas
from canvasapi.course import Course
from colorama import Fore, Style
from tabulate import tabulate
from tree_format import format_tree
from tzlocal import get_localzone

local_tz = get_localzone()

complete_cd = functools.partialmethod(cmd2.Cmd.path_complete, dir_only=True)
complete_cat = functools.partialmethod(cmd2.Cmd.path_complete, dir_only=False)

# For specifying tab-completion for default shell commands
# TODO: add basically everything from GNU Coreutils http://www.gnu.org/software/coreutils/manual/html_node/index.html
completion_map_dir_only = ['cd']
completion_map_dir_file = ['cat', 'tac', 'nl', 'od', 'base32', 'base64', 'fmt', 'tail', 'ls']

# Extend the course object to have a readable-yet-unique code that is course code + id
Course.unique_course_code = property(lambda self: self.course_code.replace(' ', '') + '-' + str(self.id))

def tabulate_dict(item_to_list, items):
    tabulate_list = tabulate(map(item_to_list, items), tablefmt='plain').split('\n')
    result = {}
    i = 0
    for item in items:
        result[item] = tabulate_list[i]
        i += 1
    return result


class Clanvas(cmd2.Cmd):
    default_to_shell = True

    def __init__(self):
        for command in completion_map_dir_only:
            setattr(Clanvas, 'complete_' + command, functools.partialmethod(cmd2.Cmd.path_complete, dir_only=True))
        for command in completion_map_dir_file:
            setattr(Clanvas, 'complete_' + command, functools.partialmethod(cmd2.Cmd.path_complete, dir_only=False))

        self.settable.update({'prompt_string': 'prompt format string'})

        super(Clanvas, self).__init__()

        self.url = None
        self.host = None
        self.canvas = None  # type: Canvas

        self.home = os.path.expanduser("~")

        self.current_course = None  # type: Course
        self.current_directory = self.home

        self.__courses = None
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
    def submission_info_items(s):
        return [s.id, s.score if hasattr(s, 'score') else '']

    @staticmethod
    def query_courses(courses, query):
        return filter(lambda course: any([query in str(item) for item in Clanvas.course_query_items(course)]), courses)

    # cmd2 attribute, made dynamic with get_prompt()
    prompt = property(lambda self: self.get_prompt())

    prompt_string = Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':' + Fore.YELLOW + '{pwc}' + Style.RESET_ALL + ':' + Fore.BLUE + '{pwd} ' + Style.RESET_ALL + '$ '

    def get_prompt(self):
        if self.canvas is None:
            return '$ '

        return self.prompt_string.format(
            login_id=(self.current_user_profile()['login_id']),
            host=(self.host),
            pwc=(self.current_course.course_code if self.current_course is not None else '~'),
            pwd=(os.getcwd().replace(self.home, '~'))
        )


    #     _____                                          _
    #    / ____|                                        | |
    #   | |     ___  _ __ ___  _ __ ___   __ _ _ __   __| |___
    #   | |    / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
    #   | |___| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
    #    \_____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/
    #

    # Reimplement POSIX cd to call os.chdir

    cd_parser = argparse.ArgumentParser()
    cd_parser.add_argument('directory', nargs='?', default='', help='absolute or relative pathname of the directory that shall become the new working directory')

    @cmd2.with_argparser(cd_parser)
    def do_cd(self, opts):
        if opts.directory == '':
            path = os.path.expanduser('~')
        else:
            path = os.path.abspath(os.path.expanduser(opts.directory))

        if not os.path.isdir(path):
            self.poutput(f'cd: no such file or directory: {path}')
        elif not os.access(path, os.R_OK):
            self.poutput(f'cd: permission denied: {path}')
        else:
            try:
                os.chdir(path)
            except Exception as ex:
                self.poutput('{}'.format(ex))

    la_parser = argparse.ArgumentParser()
    la_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
    la_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    la_parser.add_argument('-s', '--submissions', action='store_true', help='show submissions')
    la_parser.add_argument('-u', '--upcoming', action='store_true', help='show only upcoming assignments')

    @cmd2.with_argparser(la_parser)
    def do_la(self, opts):
        if self.current_course is None:
            self.poutput('Please select a course')
            return False

        course = self.current_course

        display_assignments = course.get_assignments()

        if opts.upcoming:
            now = pytz.UTC.localize(datetime.now())
            display_assignments = filter(lambda assignment: assignment.due_at_date >= now, display_assignments)

        if opts.long:
            if opts.submissions:
                assignment_ids = map(lambda assignment: assignment.id, display_assignments)
                assignment_submissions = course.list_multiple_submissions(assignment_ids=assignment_ids)

                submissions_by_assignment = defaultdict(list)

                tabulated_submissions = tabulate_dict(Clanvas.submission_info_items, assignment_submissions)
                for submission, formatted in tabulated_submissions.items():
                    submissions_by_assignment[submission.assignment_id].append((formatted, []))

                tabulated_assignments = tabulate_dict(Clanvas.assignment_info_items, display_assignments)

                tree = (course.unique_course_code, [(formatted, submissions_by_assignment[assignment.id]) for assignment, formatted in tabulated_assignments.items()])

                self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)))
            else:
                self.poutput(tabulate(map(Clanvas.assignment_info_items, display_assignments), tablefmt='plain'))
        else:
            self.poutput('\n'.join([assignment.name for assignment in display_assignments]))

    login_parser = argparse.ArgumentParser()
    login_parser.add_argument('url', help='URL of Canvas server')
    login_parser.add_argument('token', help='Canvas API access token')

    @cmd2.with_argparser(login_parser)
    def do_login(self, opts):
        if self.canvas is not None:
            self.poutput('Already logged in.')
            return False

        self.url = opts.url
        self.host = urlparse(opts.url).netloc

        self.canvas = Canvas(opts.url, opts.token)

        profile = self.current_user_profile()
        self.poutput('Logged in as {:s} ({:s})'.format(profile['name'], profile['login_id']))

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
            self.poutput(tabulate(map(Clanvas.course_info_items, display_courses), tablefmt='plain'))
        else:
            self.poutput('\n'.join([c.unique_course_code for c in display_courses]))

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
            self.poutput('Ambiguous input "{:s}".'.format(opts.course))
            self.poutput('Please select an option:')

            pad_length = len(str(num_matches)) + 2
            format_str = '{:<' + str(pad_length) + '}{}'

            self.poutput(format_str.format('0)', 'cancel'))
            count = 1
            for course in matched_courses:
                self.poutput(format_str.format(f'{count})', course.unique_course_code))
                count += 1

            choice = input('Enter number: ')
            if choice.isdigit():
                num_choice = int(choice)
                if num_choice > num_matches:
                    self.poutput(f'Choice {num_choice} greater than last choice ({num_matches}).')
                elif num_choice != 0:
                    self.current_course = matched_courses[num_choice - 1]
            else:
                self.poutput(f'Choice {choice} is not numeric.')
        else:
            self.poutput('Could not find a matching course.')

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
            self.poutput(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            self.poutput('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))


rc_file = join(os.path.expanduser('~'), '.clanvasrc')

if __name__ == '__main__':
    colorama.init()  # Windows color support

    cmd = Clanvas()
    if isfile(rc_file):
        cmd.onecmd('load ' + rc_file)
    cmd.cmdloop()
