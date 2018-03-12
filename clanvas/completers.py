import io
import shlex
import traceback
from argparse import ArgumentError
from contextlib import redirect_stderr

import cmd2
from functools import partial

import sys

from .interfaces import wopen_parser, course_query_or_cc
from .utils import unique_course_code, filter_courses


def complete_any(text, line, begidx, endidx, completers):
    for completer in completers:
        completions = completer(text, line, begidx, endidx)
        if completions:
            return completions
    return []


class Completers():
    def __init__(self, clanvas):
        self.clanvas = clanvas
        self._course_flags = dict.fromkeys(['-c', '--course'], self.course_completer)

    def course_completer(self, text, line, begidx, endidx):
        return list(map(unique_course_code, filter_courses(self.clanvas.get_courses(), line[begidx:endidx])))

    def tab_completer(self, text, line, begidx, endidx):
        try:
            f = io.StringIO()
            with redirect_stderr(f):
                opts, _ = wopen_parser.parse_known_args(shlex.split(line)[1:])
        except:
            return []

        opts.course = course_query_or_cc(self.clanvas, opts.course, fail_on_ambiguous=True, quiet=True)

        if opts.course is None:
            return []

        tabs = self.clanvas.list_tabs_cached(opts.course.id)
        matched_tabs = filter(lambda tab: tab.label.lower().startswith(opts.tab.lower()), tabs)

        return list(map(lambda tab: shlex.quote(tab.label.lower()), matched_tabs))

    def wopen_completer(self, text, line, begidx, endidx):
        return cmd2.flag_based_complete(text, line, begidx, endidx,flag_dict=self._course_flags, default_completer=self.tab_completer)