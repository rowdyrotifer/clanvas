import argparse
import os
import readline
import webbrowser
from os.path import isfile, join, expanduser
from urllib.parse import urlparse, urljoin

import cmd2
import colorama
from canvasapi import Canvas
from colorama import Fore, Style

from .filesynchronizer import FileSynchronizer
from .filters import latest_term_courses
from .lister import Lister
from .outputter import Verbosity
from .utils import *


class Clanvas(cmd2.Cmd):
    default_to_shell = True

    def __init__(self):
        self.settable.update({'prompt_string': 'prompt format string'})
        self.settable.update({'verbosity': 'default command verbosity (NORMAL/VERBOSE/DEBUG)'})

        super(Clanvas, self).__init__()

        self.url = None
        self.host = None
        self.canvas = None  # type: Canvas

        self.home = os.path.expanduser("~")

        self.current_course = None  # type: Course
        self.current_directory = self.home

        general_output_fn = functools.partial(self.poutput, end='')
        self.file_synchronizer = FileSynchronizer(general_output_fn, self.get_verbosity)
        self.lister = Lister(general_output_fn, self.get_verbosity)

    @cached_invalidatable
    def get_courses(self, **kwargs):
        return sorted(self.canvas.get_current_user().get_courses(include=['term', 'total_scores']),
                      key=lambda course: (-course.enrollment_term_id, course.name))

    @cached_invalidatable
    def current_user_profile(self, **kwargs):
        return self.canvas.get_current_user().get_profile()

    verbosity = 'NORMAL'

    def get_verbosity(self) -> Verbosity:
        return Verbosity[self.verbosity]

    # cmd2 attribute, made dynamic with get_prompt()
    prompt = property(lambda self: self.get_prompt())

    prompt_string = Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':' + Fore.YELLOW + '{pwc}' + Style.RESET_ALL + ':' + Fore.BLUE + '{pwd} ' + Style.RESET_ALL + '$ '

    def get_prompt(self):
        if self.canvas is None:
            return '$ '

        return self.prompt_string.format(
            login_id=self.current_user_profile()['login_id'],
            host=self.host,
            pwc=self.current_course.course_code if self.current_course is not None else '~',
            pwd=os.getcwd().replace(self.home, '~')
        )

    #     _____                                          _
    #    / ____|                                        | |
    #   | |     ___  _ __ ___  _ __ ___   __ _ _ __   __| |___
    #   | |    / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
    #   | |___| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
    #    \_____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/
    #

    # Reimplement POSIX cd to call os.chdir

    cd_parser = argparse.ArgumentParser(description='Change the working directory.')
    cd_parser.add_argument('directory', nargs='?', default='',
                           help='absolute or relative pathname of directory to become the new working directory')

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

    lc_parser = argparse.ArgumentParser(description='List courses.')
    lc_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
    lc_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    lc_parser.add_argument('-i', '--invalidate', action='store_true', help='invalidate cached course info')

    @cmd2.with_argparser(lc_parser)
    def do_lc(self, opts):
        courses = self.get_courses(invalidate=opts.invalidate)
        kwargs = dict(vars(opts))
        del kwargs['invalidate']
        self.lister.list_courses(courses, **kwargs)

    la_parser = argparse.ArgumentParser(description='List course assignments.')
    la_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    la_parser.add_argument('-s', '--submissions', action='store_true', help='show submissions')
    la_parser.add_argument('-u', '--upcoming', action='store_true', help='show only upcoming assignments')
    la_parser = argparser_course_optional(la_parser)

    @cmd2.with_argparser(la_parser)
    @argparser_course_optional_wrapper
    def do_la(self, opts):
        return self.lister.list_assignments(**vars(opts))

    lg_parser = argparse.ArgumentParser(description='List course grades.')
    lg_parser.add_argument('-l', '--long', action='store_true', help='long listing')
    lg_parser.add_argument('-g', '--groups', action='store_true', help='include assignment groups')
    lg_parser.add_argument('-u', '--ungraded', action='store_true', help='include ungraded assignments')
    lg_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms) if no course specified')
    lg_parser = argparser_course_optional(lg_parser)

    @cmd2.with_argparser(lg_parser)
    @argparser_course_optional_wrapper
    def do_lg(self, opts):
        opts_copy = dict(vars(opts))
        del opts_copy['all']
        if opts.course is None:
            del opts_copy['course']
            return self.lister.list_all_grades(self.get_courses() if opts.all else latest_term_courses(self.get_courses()), **opts_copy)
        else:
            return self.lister.list_grades(**opts_copy)

    lan_parser = argparse.ArgumentParser(description='List course announcements.')
    lan_parser.add_argument('-n', '--number', nargs=1, type=int, default=5, help='long listing')
    lan_parser.add_argument('-t', '--time', nargs=1, type=int, default=None, help='long listing')
    lan_parser = argparser_course_optional(lan_parser)

    @cmd2.with_argparser(lan_parser)
    @argparser_course_optional_wrapper
    def do_lan(self, opts):
        return self.lister.list_announcements(**vars(opts))

    wopen_parser = argparse.ArgumentParser(description='Open in canvas web interface.')
    wopen_parser = argparser_course_optional(wopen_parser)
    wopen_parser.add_argument('-i', '--item', default=None, help='course item to open')

    @cmd2.with_argparser(wopen_parser)
    @argparser_course_optional_wrapper
    def do_wopen(self, opts):
        if opts.course is None:
            url = self.host
        else:
            url = urljoin(self.url, f'courses/{opts.course.id}')

        if opts.item is not None and opts.course is not None:
            replace_map = {
                'home': '',
                'syllabus': 'assignments/syllabus',
                'people': 'users',
                'discussions': 'discussion_topics'
            }
            item_value = opts.item
            for item, replacement in replace_map.items():
                item_value = item_value.replace(item, replacement)
            url = urljoin(url + '/', item_value)

        webbrowser.open(url, new=2)

    login_parser = argparse.ArgumentParser(description='Set URL and token to use for all Canvas API calls')
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

    cc_parser = argparse.ArgumentParser()
    cc_parser.add_argument('course', nargs='?', default='',
                           help='course id or matching course string (e.g. the course code)')

    @cmd2.with_argparser(cc_parser)
    def do_cc(self, opts):
        if opts.course is '' or opts.course is '~':
            self.current_course = None
            return False

        match = get_course_by_query(self, opts.course)
        if match is not None:
            self.current_course = match

    def complete_cc(self, text, line, begidx, endidx):
        query = line[3:].replace(' ', '').lower()
        courses = self.get_courses()

        return [unique_course_code(course) for course in filter_courses(courses, query)]

    whoami_parser = argparse.ArgumentParser()
    whoami_parser.add_argument('-v', '--verbose', action='store_true',
                               help='display more info about the logged in user')

    @cmd2.with_argparser(whoami_parser)
    def do_whoami(self, opts):
        profile = self.canvas.get_current_user().get_profile()

        if not opts.verbose:
            self.poutput(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            self.poutput('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))

    pullf_parser = argparse.ArgumentParser(description='Pull course files to local disk.')

    @cmd2.with_argparser(argparser_course_optional(pullf_parser))
    @argparser_course_optional_wrapper
    def do_pullf(self, opts):
        if opts.course is None:
            self.poutput('No course specified.')
            return False

        code = unique_course_code(opts.course)
        files_directory = join(*[os.path.expanduser('~'), 'canvas', 'courses', code, 'files'])

        self.file_synchronizer.pull_all_files(files_directory, opts.course)


# For specifying tab-completion for default shell commands
# TODO: add basically everything from GNU Coreutils http://www.gnu.org/software/coreutils/manual/html_node/index.html

completion_map_dir_only = ['cd']
completion_map_dir_file = ['cat', 'tac', 'nl', 'od', 'base32', 'base64', 'fmt', 'tail', 'ls']

for command in completion_map_dir_only:
    setattr(Clanvas, 'complete_' + command, functools.partialmethod(cmd2.path_complete, dir_only=True))
for command in completion_map_dir_file:
    setattr(Clanvas, 'complete_' + command, functools.partialmethod(cmd2.path_complete, dir_only=False))


def main():
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind -e")
        readline.parse_and_bind("bind '\t' rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    colorama.init()  # Windows color support

    cmd = Clanvas()

    rc_file = join(expanduser('~'), '.clanvasrc')
    if isfile(rc_file):
        cmd.onecmd('load ' + rc_file)

    cmd.cmdloop()


if __name__ == "__main__":
    main()