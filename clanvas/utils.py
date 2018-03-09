import datetime
import functools
from collections import defaultdict

import pytz
from canvasapi.course import Course
from tabulate import tabulate
from tzlocal import get_localzone


def cached_invalidatable(f):
    cached_values = {}

    @functools.wraps(f)
    def check_recalculate(self, **kwargs):
        nonlocal cached_values

        kwargs_shallow_copy = {**kwargs}
        kwargs_shallow_copy.pop('invalidate', None)
        kwargs_set = frozenset(kwargs_shallow_copy)

        if kwargs.get('invalidate', False) or kwargs_set not in cached_values:
            cached_values[kwargs_set] = f(self, **kwargs)

        return cached_values[kwargs_set]

    return check_recalculate


def argparser_course_optional(argparser):
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
        if opts.course is not None:
            opts.course = get_course_by_query(self, opts.course)
        elif self.current_course is not None:
            opts.course = self.current_course

        with_argparser(self, opts)

    return inject_argparser


def rstrip_zeroes(float):
    return ('%f' % float).rstrip('0').rstrip('.')


def compact_datetime(datetime):
    return datetime.astimezone(get_localzone()).strftime("%m-%d %I:%M%p")


def unique_course_code(course):
    return course.course_code.replace(' ', '') + '-' + str(course.id)


def assignment_info_items(a):
    return [a.id, a.due_at_date.astimezone(get_localzone()).strftime("%a, %d %b %I:%M%p") if hasattr(a, 'due_at_date') else '', a.name]


def submission_info_items(s):
    return [s.id, s.score if hasattr(s, 'score') else '']

def filter_courses(courses, query):
    query_processed = query.replace(' ', '').lower()
    return filter(lambda course: query_processed in unique_course_code(course).replace(' ', '').lower(), courses)


def tabulate_dict(item_to_list, items):
    return dict(zip(items, tabulate(map(item_to_list, items), tablefmt='plain').split('\n')))

epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)

def unix_time_seconds(dt):
    return (dt - epoch).total_seconds()

def get_course_by_query(clanvas, query, fail_on_ambiguous=False, quiet=False):
    matched_courses = list(filter_courses(clanvas.get_courses(), query))
    num_matches = len(matched_courses)

    if num_matches == 1:
        return matched_courses[0]
    elif num_matches > 1 and not fail_on_ambiguous:
        if not quiet:
            clanvas.poutput('Ambiguous course input "{:s}".'.format(query))
        if not quiet:
            clanvas.poutput('Please select an option:')

        pad_length = len(str(num_matches)) + 2
        format_str = '{:<' + str(pad_length) + '}{}'

        if not quiet:
            clanvas.poutput(format_str.format('0)', 'cancel'))
        count = 1
        for course in matched_courses:
            if not quiet:
                clanvas.poutput(format_str.format(f'{count})', unique_course_code(course)))
            count += 1

        choice = input('Enter number: ')
        if choice.isdigit():
            num_choice = int(choice)
            if num_choice > num_matches:
                if not quiet:
                    clanvas.poutput(f'Choice {num_choice} greater than last choice ({num_matches}).')
            elif num_choice != 0:
                return matched_courses[num_choice - 1]
        else:
            if not quiet:
                clanvas.poutput(f'Choice {choice} is not numeric.')
    else:
        if not quiet:
            clanvas.poutput('Could not find a matching course.' if not fail_on_ambiguous else 'Ambiguous course query string.')

    return None


def get_submissions_for_assignments(course: Course, assignments):
    assignment_ids = [assignment.id for assignment in assignments]
    assignment_submissions = course.list_multiple_submissions(assignment_ids=assignment_ids)

    submissions_by_assignment = defaultdict(list)

    for submission in assignment_submissions:
        submissions_by_assignment[submission.assignment_id].append(submission)

    return submissions_by_assignment
