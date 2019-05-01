import os
import readline
import sys
import webbrowser
from functools import partialmethod
from getpass import getpass
from os import makedirs
from os.path import isfile, join, expanduser
from urllib.parse import urlparse

import cmd2
import colorama
from canvasapi import Canvas
from cmd2 import Cmd

from .completion import apply_completers
from .config import InvalidClanvasConfigurationException, parse_clanvas_config_file
from .filesynchronizer import pull_all_files
from .interfaces import *
from .lister import *
from .outputter import Verbosity, bind_outputter
from .utils import *


class Clanvas(cmd2.Cmd):
    CLANVAS_CATEGORY = 'Clanvas'

    def __init__(self, base_url, access_token, *args, **kwargs):
        super(Clanvas, self).__init__(*args, **kwargs)

        self.default_to_shell = True
        self.allow_cli_args = False

        self.settable.update({'prompt_format': 'prompt format string'})
        self.settable.update({'verbosity': 'default command verbosity (NORMAL/VERBOSE/DEBUG)'})
        self.settable.pop('prompt')

        self.url = base_url
        self.host = urlparse(base_url).netloc
        self.canvas = Canvas(base_url, access_token)  # type: Canvas

        self.home = os.path.expanduser("~")

        self.current_course = None  # type: Course

        bind_outputter(functools.partial(self.poutput, end=''), self.get_verbosity)

        apply_completers(self)

    def get_caches(self):
        return self._caches

    @blocking_lru
    def get_courses(self, **kwargs):
        return {course.id: course for course in sorted(
            self.canvas.get_current_user().get_courses(include=['term', 'total_scores']),
            key=lambda course: (-course.enrollment_term_id if hasattr(course, 'enrollment_term_id') else 0,
                                course.name if hasattr(course, 'name') else ''))}

    @blocking_lru
    def current_user_profile(self, **kwargs):
        return self.canvas.get_current_user().get_profile()

    @blocking_lru
    def list_tabs_cached(self, course_id):
        course = self.get_courses()[course_id]
        return sorted(course.get_tabs(), key=lambda tab: tab.position)

    @blocking_lru
    def list_announcements_cached(self, course_id):
        course = self.get_courses()[course_id]
        return sorted(course.get_discussion_topics(only_announcements=True), key=lambda t: t.posted_at_date)

    @blocking_lru
    def list_assignments_cached(self, course_id):
        course = self.get_courses()[course_id]
        return sorted(course.get_assignments(), key=lambda t: t.created_at_date)

    def get_verbosity(self) -> Verbosity:
        return Verbosity[self.verbosity]

    prompt_format = (Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':'
                     + Fore.LIGHTYELLOW_EX + '{pwc}' + Style.RESET_ALL + ':' + Fore.LIGHTBLUE_EX
                     + '{pwd} ' + Style.RESET_ALL + '$ ').replace('\x1b', "\\x1b")

    verbosity = 'NORMAL'

    canvas_path = expanduser('~/canvas')

    # cmd2 attribute that determines the prompt format
    prompt = property(lambda self: self.get_prompt())

    def get_prompt(self):
        if self.canvas is None:
            return '$ '

        return self.prompt_format.replace('\\x1b', '\x1b').format(
            login_id=self.current_user_profile()['login_id'],
            host=self.host,
            pwc=self.current_course.course_code if self.current_course is not None else '~',
            pwd=os.getcwd().replace(self.home, '~')
        )

    @cmd2.with_argparser(cd_parser)
    def do_cd(self, opts):
        if opts.directory == '':
            path = os.path.expanduser('~')
        else:
            path = os.path.abspath(os.path.expanduser(opts.directory))

        if not os.path.isdir(path):
            get_outputter().poutput(f'cd: no such file or directory: {path}')
        elif not os.access(path, os.R_OK):
            get_outputter().poutput(f'cd: permission denied: {path}')
        else:
            try:
                os.chdir(path)
            except Exception as ex:
                get_outputter().poutput('{}'.format(ex))

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(cc_parser)
    def do_cc(self, opts):
        if opts.course == '' or opts.course == '~':
            self.current_course = None
            return False

        match = get_course_by_query(self, opts.course)
        if match is not None:
            self.current_course = match

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(lc_parser)
    def do_lc(self, opts):
        list_courses(self.get_courses().values(), all=opts.all, long=opts.long)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(la_parser)
    @argparser_course_required_wrapper
    def do_la(self, course, opts):
        return list_assignments(course, self.list_assignments_cached, long=opts.long,
                                submissions=opts.submissions, upcoming=opts.upcoming)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(lg_parser)
    @argparser_course_required_wrapper
    def do_lg(self, course, opts):
        return list_grades(course, long=opts.long, hide_ungraded=opts.hide_ungraded)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(lann_parser)
    @argparser_course_required_wrapper
    def do_lann(self, course: Course, opts):
        return list_announcements(self.list_announcements_cached(course.id), number=opts.number,
                                  days=opts.days, print=opts.print)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(catann_parser)
    @argparser_course_required_wrapper
    def do_catann(self, course: Course, opts):
        return list_announcement(course, opts.ids)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(ua_parser)
    @argparser_course_required_wrapper
    def do_ua(self, course: Course, opts):
        try:
            assignment: Assignment = course.get_assignment(opts.id)
            get_outputter().poutput(f'Uploading submission for "{assignment.name}"')
            assignment.submit({'submission_type': 'online_upload'}, opts.file)
            get_outputter().poutput(f'Uploaded {opts.file}')
            get_outputter().poutput(f'To {assignment.html_url}')

        except ResourceDoesNotExist as e:
            get_outputter().poutput('Invalid assignment ID.')
            get_outputter().poutput_debug(f'Course {course.id} has no assignment {opts.id}')

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(wopen_parser)
    @argparser_course_required_wrapper
    def do_wopen(self, course: Course, opts):
        course_tabs = self.list_tabs_cached(course.id)
        given_tabs_set = frozenset([tab.lower() for tab in opts.tabs])

        matched_tabs = list(filter(lambda course_tab: course_tab.label.lower() in given_tabs_set, course_tabs))

        if len(matched_tabs) == 0:
            for tab in opts.tabs:
                get_outputter().poutput(f'No tab found matching "{tab}"')
            return False

        for tab in matched_tabs:
            webbrowser.open(tab.full_url, new=2)

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(whoami_parser)
    def do_whoami(self, opts):
        profile = self.canvas.get_current_user().get_profile()

        if not opts.verbose:
            get_outputter().poutput(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            get_outputter().poutput('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))

    @cmd2.with_category(CLANVAS_CATEGORY)
    @cmd2.with_argparser(pullf_parser)
    @argparser_course_required_wrapper
    def do_pullf(self, course, opts):
        code = unique_course_code(course)
        destination_path = join(
            *[os.path.expanduser('~'), 'canvas', 'courses', code, 'files']) if opts.output is None else opts.output

        pull_all_files(destination_path, course)


def is_valid_url(possible_url):
    result = urlparse(possible_url)
    return all([result.scheme, result.netloc])


def get_login_entry(destination):
    if is_valid_url(destination):
        url = destination
        history_filename = urlparse(url).netloc
        token = getpass('Enter access token: ')
    else:
        config_file = join(clanvas_dir(), 'config')
        try:
            config = parse_clanvas_config_file(config_file) if isfile(config_file) else {}
        except InvalidClanvasConfigurationException as e:
            print(f'{config_file}: {e.message}')
            print(f'{config_file}: terminating, bad configuration.')
            sys.exit(1)

        if destination in config:
            entry = config[destination]
            url = entry["url"]
            history_filename = destination
            token = entry["token"]
        else:
            print(f'No entry for name "{destination}" in clanvas config')
            sys.exit(1)

    return url, token, history_filename


def login(destination):
    url, token, history_filename = get_login_entry(destination)

    history_dir = join(clanvas_dir(), 'history')
    makedirs(history_dir, exist_ok=True)

    history_file = join(history_dir, history_filename)
    clanvas = Clanvas(url, token, persistent_history_file=history_file, persistent_history_length=5000)
    call_eagerly(clanvas.get_courses, clanvas.current_user_profile)
    return clanvas


def main():
    if 'DEBUG' in os.environ:
        import pydevd
        pydevd.settrace('localhost', suspend=False, port=5678)

    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind -e")
        readline.parse_and_bind("bind '\t' rl_complete")

    colorama.init()  # Windows color support

    makedirs(clanvas_dir(), exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument('destination', help='Canvas URL or the hostname of entry from Clanvas config')
    args = parser.parse_args()

    clanvas = login(args.destination)
    clanvas.cmdloop()


if __name__ == "__main__":
    main()
