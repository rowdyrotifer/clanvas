import datetime
import functools
import threading
from collections import defaultdict

import pytz
from canvasapi.course import Course
from tabulate import tabulate
from tzlocal import get_localzone


def rstrip_zeroes(float_var):
    return ('%f' % float_var).rstrip('0').rstrip('.')


def compact_datetime(datetime_var):
    return datetime_var.astimezone(get_localzone()).strftime("%m-%d %I:%M%p")


def percentage_string(val, digits):
    val *= 10 ** (digits + 2)
    return '{1:.{0}f}%'.format(digits, val / 10 ** digits)


def rstripped_fraction(score, possible):
    numerator = rstrip_zeroes(score) if type(score) == float else str(score)
    denominator = rstrip_zeroes(possible) if type(possible) == float else str(possible)
    return f'{numerator}/{denominator}'


def unique_course_code(course):
    return course.course_code.replace(' ', '') + '-' + str(course.id)


def assignment_info_items(a):
    return [a.id, compact_datetime(a.due_at_date) if hasattr(a, 'due_at_date') else '', a.name]


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
    matched_courses = list(filter_courses(clanvas.get_courses().values(), query))
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


def call_eagerly(*args):
    def runner(stop_event, callables):
        while not stop_event.is_set() and callables:
            callables.pop()()

    event = threading.Event()
    thread = threading.Thread(target=runner, args=(event, list(args)))
    thread.start()
    return event


def blocking_lru(func):
    func = functools.lru_cache(maxsize=None)(func)
    lock_dict = defaultdict(threading.Lock)

    def _thread_lru(*args, **kwargs):
        key = functools._make_key(args, kwargs, typed=False)
        with lock_dict[key]:
            return func(*args, **kwargs)

    return _thread_lru


def get_submissions_for_assignments(course: Course, assignments):
    assignment_ids = [assignment.id for assignment in assignments]
    assignment_submissions = course.list_multiple_submissions(assignment_ids=assignment_ids)

    submissions_by_assignment = defaultdict(list)

    for submission in assignment_submissions:
        submissions_by_assignment[submission.assignment_id].append(submission)

    return submissions_by_assignment
