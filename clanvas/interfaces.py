import argparse
import functools

from .outputter import get_outputter
from .utils import get_course_by_query


def course_query_or_cc(clanvas, course, fail_on_ambiguous=False, quiet=False):
    if course is not None:
        return get_course_by_query(clanvas, course, fail_on_ambiguous=fail_on_ambiguous, quiet=quiet)
    elif clanvas.current_course is not None:
        return clanvas.current_course
    else:
        return None


course_actions = []


def course_optional(argparser):
    action = argparser.add_argument('-c', '--course', default=None, help='course id or matching course code substring')
    course_actions.append(action)


def argparser_course_required_wrapper(with_argparser):
    """
    When applied to a do_x function in the Clanvas class that takes in argparser opts,
    will convert/replace course attribute with a corresponding course object either
    using the course string as a query or the current (cc'd) course if not supplied.
    :param with_argparser: the cmd2.with_argparser method to be wrapped.
    :return:
    """
    @functools.wraps(with_argparser)
    def inject_argparser(self, opts, *args, **kwargs):
        course = course_query_or_cc(self, opts.course)
        if course is None:
            get_outputter().poutput('Please specify a course to use this command.')
            get_outputter().poutput_verbose('Use the cc command or the -c option.')
            return False
        else:
            delattr(opts, 'course')
            return with_argparser(self, course, opts, *args, **kwargs)

    return inject_argparser


DEFAULT = '__DEFAULT__'

course_option_parser = argparse.ArgumentParser()
course_optional(course_option_parser)

cc_parser = argparse.ArgumentParser()
cc_parser_course_action = cc_parser.add_argument('course', nargs='?', default='',
                                                 help='course id or matching course string (e.g. the course code)')
course_actions.append(cc_parser_course_action)

cd_parser = argparse.ArgumentParser(description='Change the working directory.')
cd_parser_directory_action = cd_parser.add_argument('directory', nargs='?', default='',
                       help='absolute or relative pathname of directory to become the new working directory')

lc_parser = argparse.ArgumentParser(description='List courses.')
lc_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
lc_parser.add_argument('-l', '--long', action='store_true', help='long listing')

la_parser = argparse.ArgumentParser(description='List course assignments.')
course_optional(la_parser)
la_parser.add_argument('-l', '--long', action='store_true', help='long listing')
la_parser.add_argument('-s', '--submissions', action='store_true', help='show submissions')
la_parser.add_argument('-u', '--upcoming', action='store_true', help='show only upcoming assignments')

lann_parser = argparse.ArgumentParser(description='List course announcements.')
course_optional(lann_parser)
lann_parser.add_argument('-n', '--number', type=int, default=None, help='number of announcements to display')
lann_parser.add_argument('-d', '--days', type=int, default=None, help='only show announcements this many days old')
lann_parser.add_argument('-p', '--print', action='store_true', help='print out body of announcements in list')

catann_parser = argparse.ArgumentParser(description='Print course announcements.')
course_optional(catann_parser)
catann_parser_ids_action = catann_parser.add_argument('ids', nargs='*', help='ids of announcements to print')

lg_parser = argparse.ArgumentParser(description='List course grades.')
course_optional(lg_parser)
lg_parser.add_argument('-l', '--long', action='store_true', help='long listing')
lg_parser.add_argument('-u', '--hide-ungraded', action='store_true', help='hide ungraded assignments')

login_parser = argparse.ArgumentParser(description='Set URL and token to use for all Canvas API calls')
login_parser.add_argument('url', help='URL of Canvas server')
login_parser.add_argument('token', help='Canvas API access token')
login_parser.add_argument('-q', '--quiet', action='store_true', help='suppress login message')

pullf_parser = argparse.ArgumentParser(description='Pull course files to local disk.')
course_optional(pullf_parser)
pullf_parser_output_action = pullf_parser.add_argument('-o', '--output', help='location to save course files')

ua_parser = argparse.ArgumentParser(description='Upload a submission to an assignment')
course_optional(ua_parser)
ua_parser_id_action = ua_parser.add_argument('id', type=int, help='id of assignment to upload a submission to')
ua_parser_file_action = ua_parser.add_argument('file', default=None, help='file to submit')

whoami_parser = argparse.ArgumentParser()
whoami_parser.add_argument('-v', '--verbose', action='store_true',
                           help='display more info about the logged in user')

wopen_parser = argparse.ArgumentParser(description='Open tabs in canvas web interface.')
course_optional(wopen_parser)
wopen_parser_tabs_action = wopen_parser.add_argument('tabs', nargs='*', default='', help='course tabs to open')
