from functools import lru_cache
from operator import itemgetter

from canvasapi.assignment import Assignment, AssignmentGroup
from canvasapi.exceptions import Unauthorized, CanvasException, ResourceDoesNotExist
from canvasapi.submission import Submission
from colorama import Fore, Style, Back
from html2text import html2text
from tree_format import format_tree

from .utils import *


def calculate_group_ratio(group, assignment_submission_pairs):
    # Memoize by sticking it in the group... maybe this is totally pointless though since arithmetic ops are cheap
    if hasattr(group, 'clanvas_total_points'):
        return group.clanvas_ratio, group.clanvas_total_points, group.clanvas_total_possible

    total_points = sum([(s.score if s is not None else 0) for (a, s) in assignment_submission_pairs])
    total_possible = sum([(a.points_possible if s is not None else 0) for (a, s) in assignment_submission_pairs])
    ratio = total_points / total_possible if total_possible != 0 else None
    group.clanvas_total_points = total_points
    group.clanvas_total_possible = total_possible
    group.clanvas_ratio = ratio
    return ratio, total_points, total_possible


def list_courses(courses, all=False, long=False):
    display_courses = courses if all else filter_latest_term_courses(courses)

    if display_courses:
        if long:
            def course_info_items(c):
                return [c.course_code,
                        c.id,
                        c.term['name'] if hasattr(c, 'term') else '',
                        c.name if hasattr(c, 'name') else '']

            get_outputter().poutput(tabulate(map(course_info_items, display_courses), tablefmt='plain'))
        else:
            get_outputter().poutput('\n'.join([unique_course_code(c) for c in display_courses]))
    else:
        get_outputter().poutput('No courses available.')


def list_assignments(course: Course, assignments_provider, long=False, submissions=False, upcoming=False):
    assignments = assignments_provider(course.id)

    if upcoming:
        assignments = filter_future_assignments(assignments)

    if long:
        if submissions:
            assignment_ids = map(lambda assignment: assignment.id, assignments)
            assignment_submissions = course.get_multiple_submissions(assignment_ids=assignment_ids)

            submissions_by_assignment = defaultdict(list)

            tabulated_submissions = tabulate_dict(submission_info_items, assignment_submissions)
            for submission, formatted in tabulated_submissions.items():
                submissions_by_assignment[submission.assignment_id].append((formatted, []))

            tabulated_assignments = tabulate_dict(assignment_info_items, assignments)

            tree = (unique_course_code(course), [(formatted, submissions_by_assignment[assignment.id]) for assignment, formatted in tabulated_assignments.items()])

            get_outputter().poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)))
        else:
            get_outputter().poutput(tabulate(map(assignment_info_items, assignments), tablefmt='plain'))
    else:
        get_outputter().poutput('\n'.join([assignment.name for assignment in assignments]))


grade_color_thresholds = {
    0.9: Fore.LIGHTGREEN_EX,
    0.8: Fore.MAGENTA,
    0.7: Fore.YELLOW,
    0.6: Fore.LIGHTRED_EX,
    0.0001: Fore.RED,
    0.0: Back.RED + Fore.BLACK
}


def best_color(ratio):
    for key, value in grade_color_thresholds.items():
        if ratio >= key:
            return value


def tabulate_grade_row(assignment, submission, long):
    possible = assignment.points_possible
    if submission is not None:
        score = submission.score
        fraction = rstripped_fraction(score, possible)
        if possible != 0:
            ratio = score / possible
            percentage = percentage_string(ratio, 0)
            color = best_color(ratio)
        else:
            percentage = 'N/A'
            color = ''

        def colored(string):
            return color + str(string) + Style.RESET_ALL
    else:
        fraction = rstripped_fraction('?', possible)
        percentage = ''

        def colored(string):
            return string

    if long:
        due_at_str = compact_datetime(assignment.due_at_date) if hasattr(assignment, 'due_at_date') else ''
        return [colored(string) for string in [submission.id if submission is not None else 'Unsubmitted', due_at_str, assignment.name, fraction, percentage]]
    else:
        return [colored(string) for string in [assignment.name, fraction, percentage]]


def grades_tree(course: Course):
    assignment_submission_pair = course.get_assignments()
    submissions_by_assignment = get_submissions_for_assignments(course, assignment_submission_pair)

    def graded_submission(assignment):
        if assignment.id in submissions_by_assignment:
            submissions = submissions_by_assignment[assignment.id]
            submission = next((s for s in submissions if hasattr(s, 'grade') and s.grade is not None), None)
            if submission is not None:
                return submission
        return None

    graded_assignment_submissions = {assignment: graded_submission(assignment) for assignment in assignment_submission_pair}

    tree_items = []
    assignment_groups = course.get_assignment_groups()

    grouped_assignment_submission_pairs = {}
    for assignment, submission in graded_assignment_submissions.items():
        if assignment.assignment_group_id not in grouped_assignment_submission_pairs:
            grouped_assignment_submission_pairs[assignment.assignment_group_id] = []
        grouped_assignment_submission_pairs[assignment.assignment_group_id].append((assignment, submission))

    for group in sorted(assignment_groups, key=lambda g: g.position):
        assignment_submission_pair = grouped_assignment_submission_pairs[group.id]\
            if group.id in grouped_assignment_submission_pairs else []
        group_subtree = (group, assignment_submission_pair)
        tree_items.append(group_subtree)

    return course, tree_items


def list_grades(course: Course, long=False, hide_ungraded=False):
    try:
        tree = grades_tree(course)

        @lru_cache(maxsize=None)
        def group_ratio(id):
            pass

        def format_node(node):
            item = node[0]
            if isinstance(item, Course):
                course = item
                groups_item = node[1]

                course_name = course_name_or_unique_course_code(course)

                def weighted_contribution(group, assignment_submission_pairs):
                    ratio = calculate_group_ratio(group, assignment_submission_pairs)[0]
                    return (group.group_weight/100) * ratio if ratio is not None else group.group_weight/100

                weighted_sum = sum(weighted_contribution(group, assignments) for (group, assignments) in groups_item)
                if weighted_sum > 0:
                    percentage = percentage_string(weighted_sum, 1)
                    color = best_color(weighted_sum) if weighted_sum > 0 else ''
                    return color + course_name + ' ' + percentage + Style.RESET_ALL
                else:
                    return course_name
            elif isinstance(item, AssignmentGroup):
                group = item
                assignment_submission_pairs = node[1]

                ratio, total_points, total_possible = calculate_group_ratio(group, assignment_submission_pairs)

                fraction = rstripped_fraction(total_points, total_possible)
                if total_possible != 0:
                    ratio = total_points / total_possible
                    percentage = percentage_string(ratio, 1)
                    color = best_color(ratio)
                else:
                    percentage = 'N/A'
                    color = ''

                if long:
                    items = [group.name, f'(Weight={percentage_string(group.group_weight/100, 0)})', fraction, percentage]
                else:
                    items = [group.name, fraction, percentage]

                return color + ' '.join(items) + Style.RESET_ALL
            elif isinstance(item, Assignment):
                assignment, submission = node
                return ' '.join([str(x) for x in tabulate_grade_row(assignment, submission, long=long)])

        def get_children(node):
            if isinstance(node[1], Submission) or node[1] is None:
                return []
            else:
                return list(filter(lambda item: not hide_ungraded or item[1] is not None, node[1]))

        get_outputter().poutput(format_tree(tree, format_node=format_node, get_children=get_children), end='')
    except Unauthorized:
        get_outputter().poutput(f'{course_name_or_unique_course_code(course)}: Unauthorized')
    except CanvasException as e:
        get_outputter().poutput(f'{course_name_or_unique_course_code(course)}: {str(e)}')


def list_announcements(display_topics, number=None, days=None, print=False):
    if number is not None:
        display_topics = display_topics[-number:]

    if days is not None:
        display_topics = filter_days_from_today(display_topics, days, key=lambda t: t.posted_at_date)

    if print:
        def print_topic(topic):
            return '\n'.join([topic.user_name, topic.title, html2text('\n'.join(topic.message.splitlines())).strip()])
        output = '\n=================\n'.join(map(print_topic, display_topics))
    else:
        def topic_row(topic):
            return [topic.id, compact_datetime(topic.posted_at_date), topic.user_name, topic.title]
        output = tabulate(map(topic_row, display_topics), tablefmt='plain')

    get_outputter().poutput(output)

    return False


def list_announcement(course: Course, ids):
    for announcement_id in ids:
        try:
            topic = course.get_discussion_topic(int(announcement_id))

            body = html2text('\n'.join(topic.message.splitlines())).strip()

            print_items = [topic.user_name,
                           long_datetime(topic.posted_at_date),
                           topic.title,
                           '',
                           body]

            get_outputter().poutput('\n'.join(print_items))
        except ResourceDoesNotExist:
            get_outputter().poutput(f'{str(announcement_id)}: no such'
                                   f'announcement id for {unique_course_code(course)}')
