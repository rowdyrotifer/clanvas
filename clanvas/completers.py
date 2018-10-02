import functools
import io
import shlex
from contextlib import redirect_stderr

from .interfaces import wopen_parser, course_query_or_cc, catann_parser
from .utils import unique_course_code, filter_courses


def complete_any(text, line, begidx, endidx, completers):
    for completer in completers:
        completions = completer(text, line, begidx, endidx)
        if completions:
            return completions
    return []


def parse_partial(argparser, line):
    try:
        stream = io.StringIO()
        with redirect_stderr(stream):
            opts, _ = argparser.parse_known_args(shlex.split(line)[1:])
            return opts
    except ValueError as e:
        if str(e) == 'No closing quotation':
            print(line + '\'')
            return parse_partial(argparser, line + '\'')
    except:
        import traceback
        traceback.print_exc()
        return None


class Completers:
    def __init__(self, clanvas):
        self.clanvas = clanvas
        self._course_complete_flags = dict.fromkeys(['-c', '--course'], self._course_completer)

        self.completer_mapping = {
            'catann': functools.partial(self._course_option_completer, all_else=self._catann_tab_completer),
            'cc': self._course_completer,
            'cd': functools.partial(self.clanvas.path_complete, dir_only=True),
            'la': self._course_option_completer,
            'lann': self._course_option_completer,
            'lg': self._course_option_completer,
            'pullf': self._pullf_tab_completer,
            'wopen': functools.partial(self._course_option_completer, all_else=self._wopen_tab_completer)
        }

    def _course_completer(self, text, line, begidx, endidx):
        return list(map(unique_course_code, filter_courses(self.clanvas.get_courses().values(), line[begidx:endidx])))

    def _catann_tab_completer(self, text, line, begidx, endidx):
        opts = parse_partial(catann_parser, line[0:endidx])
        if opts is None:
            return []

        opts.course = course_query_or_cc(self.clanvas, opts.course, fail_on_ambiguous=True, quiet=True)
        if opts.course is None:
            return []

        matching_string = '' if len(opts.ids) == 0 or line[endidx-1] == ' ' else opts.ids[-1]

        announcements = [str(ann.id) for ann in self.clanvas.list_announcements_cached(opts.course.id)]
        matched_announcements = filter(lambda ann: ann.startswith(matching_string), announcements)

        return list(matched_announcements)

    def _wopen_tab_completer(self, text, line, begidx, endidx):
        opts = parse_partial(wopen_parser, line[0:endidx])
        if opts is None:
            return []

        opts.course = course_query_or_cc(self.clanvas, opts.course, fail_on_ambiguous=True, quiet=True)
        if opts.course is None:
            return []

        matching_string = '' if len(opts.tabs) == 0 or line[endidx-1] == ' ' else opts.tabs[-1]

        tabs = self.clanvas.list_tabs_cached(opts.course.id)
        matched_tabs = filter(lambda tab: tab.label.lower().startswith(matching_string.lower()), tabs)
        return list(map(lambda tab: shlex.quote(tab.label.lower()), matched_tabs))

    def _course_option_completer(self, text, line, begidx, endidx, all_else=None):
        return self.clanvas.flag_based_complete(
            text, line, begidx, endidx, flag_dict=self._course_complete_flags, all_else=all_else)

    def _pullf_tab_completer(self, text, line, begidx, endidx):
        output_flags = dict.fromkeys(['-o', '--output'], functools.partial(self.clanvas.path_complete, dir_only=True))
        return self.clanvas.flag_based_complete(text, line, begidx, endidx, flag_dict={
            **self._course_complete_flags,
            **output_flags})
