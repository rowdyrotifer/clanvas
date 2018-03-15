import os
import webbrowser
from os.path import isfile, join, expanduser
from urllib.parse import urlparse

import cmd2
import colorama
import readline
from canvasapi import Canvas
from colorama import Fore, Style

from .completers import Completers
from .filesynchronizer import FileSynchronizer
from .filters import latest_term_courses
from .interfaces import *
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
        self.completers = Completers(self)

        self.complete_cc = self.completers.course_completer
        self.complete_wopen = self.completers.wopen_completer
        self.complete_pullf = self.completers.pullf_completer

        self.complete_la = self.completers.generic_course_optional_completer
        self.complete_lg = self.completers.generic_course_optional_completer
        self.complete_lan = self.completers.generic_course_optional_completer

    @blocking_lru
    def get_courses(self, **kwargs):
        return {course.id: course for course in sorted(self.canvas.get_current_user().get_courses(include=['term', 'total_scores']),
                      key=lambda course: (-course.enrollment_term_id, course.name))}

    @blocking_lru
    def current_user_profile(self, **kwargs):
        return self.canvas.get_current_user().get_profile()

    @blocking_lru
    def list_tabs_cached(self, course_id):
        course = self.get_courses()[course_id]
        return sorted(course.list_tabs(), key=lambda tab: tab.position)

    def get_verbosity(self) -> Verbosity:
        return Verbosity[self.verbosity]

    prompt_string = Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':' + Fore.YELLOW + '{pwc}' + Style.RESET_ALL + ':' + Fore.BLUE + '{pwd} ' + Style.RESET_ALL + '$ '

    verbosity = 'NORMAL'

    canvas_path = expanduser('~/canvas')

    def get_prompt(self):
        if self.canvas is None:
            return '$ '

        return self.prompt_string.format(
            login_id=self.current_user_profile()['login_id'],
            host=self.host,
            pwc=self.current_course.course_code if self.current_course is not None else '~',
            pwd=os.getcwd().replace(self.home, '~')
        )


    # cmd2 attribute
    prompt = property(lambda self: self.get_prompt())

    #     _____                                          _
    #    / ____|                                        | |
    #   | |     ___  _ __ ___  _ __ ___   __ _ _ __   __| |___
    #   | |    / _ \| '_ ` _ \| '_ ` _ \ / _` | '_ \ / _` / __|
    #   | |___| (_) | | | | | | | | | | | (_| | | | | (_| \__ \
    #    \_____\___/|_| |_| |_|_| |_| |_|\__,_|_| |_|\__,_|___/
    #

    # Reimplement POSIX cd to call os.chdir

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

    @cmd2.with_argparser(cc_parser)
    def do_cc(self, opts):
        if opts.course is '' or opts.course is '~':
            self.current_course = None
            return False

        match = get_course_by_query(self, opts.course)
        if match is not None:
            self.current_course = match

    @cmd2.with_argparser(lc_parser)
    def do_lc(self, opts):
        courses = self.get_courses().values()
        kwargs = dict(vars(opts))
        del kwargs['invalidate']
        self.lister.list_courses(courses, **kwargs)

    @cmd2.with_argparser(la_parser)
    @argparser_course_optional_wrapper
    def do_la(self, opts):
        return self.lister.list_assignments(**vars(opts))

    @cmd2.with_argparser(lg_parser)
    @argparser_course_optional_wrapper
    def do_lg(self, opts):
        opts_copy = dict(vars(opts))
        del opts_copy['all']
        if opts.course is None:
            del opts_copy['course']
            courses = self.get_courses().values() if opts.all else latest_term_courses(self.get_courses().values())
            for course in courses:
                self.lister.list_grades(course, **opts_copy)
        else:
            return self.lister.list_grades(**opts_copy)

    @cmd2.with_argparser(lan_parser)
    @argparser_course_optional_wrapper
    def do_lan(self, opts):
        return self.lister.list_announcements(**vars(opts))


    @cmd2.with_argparser(wopen_parser)
    @argparser_course_optional_wrapper
    def do_wopen(self, opts):
        if opts.tab is not None and opts.course is not None:
            tabs = self.list_tabs_cached(opts.course.id)

            matched_tab = next(filter(lambda tab: opts.tab.lower() in tab.label.lower(), tabs), None)
            if matched_tab is None:
                self.poutput(f'No tab found matching {opts.tab}')
                return False

            webbrowser.open(matched_tab.full_url, new=2)


        return False

    @cmd2.with_argparser(login_parser)
    def do_login(self, opts):
        if self.canvas is not None:
            self.poutput('Already logged in.')
            return False

        self.url = opts.url
        self.host = urlparse(opts.url).netloc

        self.canvas = Canvas(opts.url, opts.token)

        if not opts.quiet:
            profile = self.current_user_profile()
            self.poutput('Logged in as {:s} ({:s})'.format(profile['name'], profile['login_id']))
            call_eagerly(self.get_courses)
        else:
            call_eagerly(self.get_courses, self.current_user_profile)

    @cmd2.with_argparser(whoami_parser)
    def do_whoami(self, opts):
        profile = self.canvas.get_current_user().get_profile()

        if not opts.verbose:
            self.poutput(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            self.poutput('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))

    @cmd2.with_argparser(pullf_parser)
    @argparser_course_optional_wrapper
    def do_pullf(self, opts):
        if opts.course is None:
            self.poutput('No course specified.')
            return False

        code = unique_course_code(opts.course)
        destination_path = join(*[os.path.expanduser('~'), 'canvas', 'courses', code, 'files']) if opts.output is None else opts.output

        self.file_synchronizer.pull_all_files(destination_path, opts.course)


# For specifying tab-completion for default shell commands
# TODO: add basically everything from GNU Coreutils http://www.gnu.org/software/coreutils/manual/html_node/index.html
# Better TODO: make shell completion default to

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

    colorama.init()  # Windows color support

    cmd = Clanvas()

    rc_file = join(expanduser('~'), '.clanvasrc')
    if isfile(rc_file):
        cmd.onecmd('load ' + rc_file)

    cmd.cmdloop()


if __name__ == "__main__":
    main()