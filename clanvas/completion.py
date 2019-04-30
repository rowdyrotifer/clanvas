import io
import os
import shlex
from contextlib import redirect_stderr
from functools import partial, wraps

from cmd2.argparse_completer import CompletionItem

from .interfaces import course_query_or_cc, course_option_parser, course_actions, \
    catann_parser_ids_action, wopen_parser_tabs_action, pullf_parser_output_action, ua_parser_id_action, \
    ua_parser_file_action, cd_parser_directory_action
from .utils import unique_course_code, filter_courses


def parse_partial(argparser, line):
    try:
        stream = io.StringIO()
        with redirect_stderr(stream):
            opts, _ = argparser.parse_known_args(shlex.split(line)[1:])
            return opts
    except ValueError as e:
        if str(e) == 'No closing quotation':
            return parse_partial(argparser, line + ('"' if line.rfind('"') > line.rfind("'") else "'"))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    return None


def course_required_completer(completer_function):
    @wraps(completer_function)
    def call_with_course(text, line, begidx, endidx, clanvas):
        opts = parse_partial(course_option_parser, line)
        if opts is None:
            return []

        course = course_query_or_cc(clanvas, opts.course, fail_on_ambiguous=True, quiet=True)
        if course is None:
            return []

        return completer_function(text, line, begidx, endidx, course, clanvas)

    return call_with_course


def _course_completer(text, line, begidx, endidx, clanvas):
    courses = filter_courses(clanvas.get_courses().values(), query=line[begidx:endidx])

    def completion_item(course):
        return CompletionItem(unique_course_code(course), course.name if hasattr(course, 'name') else '')
    return [completion_item(course) for course in courses]


def apply_completers(clanvas):
    catann_parser_ids_action.arg_choices = (_catann_tab_completer, [clanvas])
    catann_parser_ids_action.desc_header = 'Title'

    cd_parser_directory_action.arg_choices = (partial(clanvas.path_complete, path_filter=os.path.isdir), None)

    pullf_parser_output_action.arg_choices = (partial(clanvas.path_complete, path_filter=os.path.isdir), None)

    ua_parser_id_action.arg_choices = (_assignment_completer, [clanvas])
    ua_parser_id_action.desc_header = 'Name'

    ua_parser_file_action.arg_choices = (clanvas.path_complete, None)

    wopen_parser_tabs_action.arg_choices = (_wopen_tab_completer, [clanvas])

    for course_complete_action in course_actions:
        course_complete_action.arg_choices = (_course_completer, [clanvas])
        course_complete_action.desc_header = 'Name'


# TODO: radix tree for more CPU efficiency at the cost of memory efficiency?

def startswith_completer(input, iterable, case_sensitive=False):
    return list(filter(lambda item: (item if case_sensitive else item.lower())
                       .startswith((input if case_sensitive else input.lower())), iterable))


@course_required_completer
def _assignment_completer(text, line, begidx, endidx, course, clanvas):
    def completion_item(assignment):
        return CompletionItem(str(assignment.id), assignment.name if hasattr(assignment, 'name') else '')
    return startswith_completer(line[begidx:endidx],
                                [completion_item(assignment) for assignment in clanvas.list_assignments_cached(course.id)])


@course_required_completer
def _catann_tab_completer(text, line, begidx, endidx, course, clanvas):
    def completion_item(announcement):
        return CompletionItem(str(announcement.id), announcement.title if hasattr(announcement, 'title') else '')
    return startswith_completer(line[begidx:endidx],
                                [completion_item(ann) for ann in clanvas.list_announcements_cached(course.id)])


@course_required_completer
def _wopen_tab_completer(text, line, begidx, endidx, course, clanvas):
    return startswith_completer(line[begidx:endidx],
                                [tab.label for tab in clanvas.list_tabs_cached(course.id)])
