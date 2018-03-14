import argparse
import functools

from .utils import get_course_by_query


def course_query_or_cc(clanvas, course, fail_on_ambiguous=False, quiet=False):
    if course is not None:
        return get_course_by_query(clanvas, course, fail_on_ambiguous=fail_on_ambiguous, quiet=quiet)
    elif clanvas.current_course is not None:
        return clanvas.current_course
    else:
        return None


def course_optional(argparser):
    argparser.add_argument('-c', '--course', default=None, help='course id or matching course code substring')
    return argparser


def argparser_course_optional_wrapper(with_argparser):
    """
    When applied to a do_x function in the Clanvas class that takes in argparser opts,
    will convert/replace course attribute with a corresponding course object either
    using the course string as a query or the current (cc'd) course if not supplied.
    :param with_argparser: the cmd2.with_argparser method to be wrapped.
    :return:
    """
    @functools.wraps(with_argparser)
    def inject_argparser(self, opts):
        opts.course = course_query_or_cc(self, opts.course)

        with_argparser(self, opts)

    return inject_argparser

DEFAULT = '__DEFAULT__'

cc_parser = argparse.ArgumentParser()
cc_parser.add_argument('course', nargs='?', default='',
                       help='course id or matching course string (e.g. the course code)')

cd_parser = argparse.ArgumentParser(description='Change the working directory.')
cd_parser.add_argument('directory', nargs='?', default='',
                       help='absolute or relative pathname of directory to become the new working directory')

lc_parser = argparse.ArgumentParser(description='List courses.')
lc_parser.add_argument('-a', '--all', action='store_true', help='all courses (previous terms)')
lc_parser.add_argument('-l', '--long', action='store_true', help='long listing')
lc_parser.add_argument('-i', '--invalidate', action='store_true', help='invalidate cached course info')

la_parser = argparse.ArgumentParser(description='List course assignments.')
la_parser = course_optional(la_parser)
la_parser.add_argument('-l', '--long', action='store_true', help='long listing')
la_parser.add_argument('-s', '--submissions', action='store_true', help='show submissions')
la_parser.add_argument('-u', '--upcoming', action='store_true', help='show only upcoming assignments')

lan_parser = argparse.ArgumentParser(description='List course announcements.')
lan_parser = course_optional(lan_parser)
lan_parser.add_argument('-n', '--number', nargs=1, type=int, default=5, help='long listing')
lan_parser.add_argument('-t', '--time', nargs=1, type=int, default=None, help='long listing')

lg_parser = argparse.ArgumentParser(description='List course grades.')
lg_parser = course_optional(lg_parser)
lg_parser.add_argument('-l', '--long', action='store_true', help='long listing')
lg_parser.add_argument('-u', '--ungraded', action='store_false', help='include ungraded assignments')
lg_parser.add_argument('-a', '--all', action='store_true', help='show grades for all courses (previous terms) if no course is specified')

login_parser = argparse.ArgumentParser(description='Set URL and token to use for all Canvas API calls')
login_parser.add_argument('url', help='URL of Canvas server')
login_parser.add_argument('token', help='Canvas API access token')
login_parser.add_argument('-q', '--quiet', action='store_true', help='suppress login message')

pullf_parser = argparse.ArgumentParser(description='Pull course files to local disk.')
pullf_parser = course_optional(pullf_parser)
pullf_parser.add_argument('-o', '--output', help='location to save course files')

whoami_parser = argparse.ArgumentParser()
whoami_parser.add_argument('-v', '--verbose', action='store_true',
                           help='display more info about the logged in user')

wopen_parser = argparse.ArgumentParser(description='Open in canvas web interface.')
wopen_parser = course_optional(wopen_parser)
wopen_parser.add_argument('tab', nargs='?', default='', help='course tab to open')