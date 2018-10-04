import functools
import io
import shlex
from contextlib import redirect_stderr

from cmd2.argparse_completer import AutoCompleter

from .interfaces import wopen_parser, course_query_or_cc, catann_parser, ua_parser, course_option_parser, pullf_parser, \
    lg_parser, lann_parser, la_parser, cd_parser, cc_parser
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
    @functools.wraps(completer_function)
    def call_with_course(text, line, begidx, endidx, clanvas):
        opts = parse_partial(course_option_parser, line)
        if opts is None:
            return []

        course = course_query_or_cc(clanvas, opts.course, fail_on_ambiguous=True, quiet=True)
        if course is None:
            return []

        return completer_function(text, line, begidx, endidx, course, clanvas)

    return call_with_course


def create_completer(completer_data, cmd2_app):
    def completer_implementation(text, line, begidx, endidx):
        if isinstance(completer_data, tuple):
            parser, choices = completer_data
            completer = AutoCompleter(parser, cmd2_app=cmd2_app, arg_choices=choices)
            tokens, _ = cmd2_app.tokens_for_completion(line, begidx, endidx)
            results = completer.complete_command(tokens, text, line, begidx, endidx)
            return results
        else:
            return completer_data(text, line, begidx, endidx)

    return completer_implementation


def with_course_optional(clanvas, choices={}):
    return {'course': (_course_completer,[clanvas]), **choices}


def _course_completer(text, line, begidx, endidx, clanvas):
    return list(map(unique_course_code, filter_courses(clanvas.get_courses().values(), line[begidx:endidx])))


def get_completer_mapping(clanvas):
    return {key: create_completer(completer_data, clanvas) for key, completer_data in {
        'catann': (catann_parser, with_course_optional(clanvas, {
            'ids': (_catann_tab_completer, [clanvas])
        })),
        'cc': (cc_parser, {
            'course': (_course_completer, [clanvas])
        }),
        'cd': (cd_parser, with_course_optional(clanvas, {
            'directory': (clanvas.path_complete, [True])
        })),
        'la': (la_parser, with_course_optional(clanvas, {})),
        'lann': (lann_parser, with_course_optional(clanvas, {})),
        'lg': (lg_parser, with_course_optional(clanvas, {})),
        'pullf': (pullf_parser, with_course_optional(clanvas, {
            'output': (clanvas.path_complete, [True])
        })),
        'ua': (ua_parser, with_course_optional(clanvas, {
            'id': (_assignment_completer, [clanvas]),
            'file': (clanvas.path_complete,)
        })),
        'wopen': (wopen_parser, with_course_optional(clanvas, {
            'tabs': (_wopen_tab_completer, [clanvas])
        }))
        }.items()}


# TODO: radix tree for more CPU efficiency at the cost of memory efficiency?

def startswith_completer(input, iterable, case_sensitive=False):
    return list(filter(lambda item: (item if case_sensitive else item.lower())
                       .startswith((input if case_sensitive else input.lower())), iterable))


@course_required_completer
def _assignment_completer(text, line, begidx, endidx, course, clanvas):
    return startswith_completer(line[begidx:endidx],
                                [str(assignment.id) for assignment in clanvas.list_assignments_cached(course.id)])


@course_required_completer
def _catann_tab_completer(text, line, begidx, endidx, course, clanvas):
    return startswith_completer(line[begidx:endidx],
                                [str(ann.id) for ann in clanvas.list_announcements_cached(course.id)])


@course_required_completer
def _wopen_tab_completer(text, line, begidx, endidx, course, clanvas):
    return startswith_completer(line[begidx:endidx],
                                [tab.label for tab in clanvas.list_tabs_cached(course.id)])
