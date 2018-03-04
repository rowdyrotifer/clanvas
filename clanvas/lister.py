from datetime import datetime
from collections import defaultdict
from operator import itemgetter

import pytz
from canvasapi.course import Course
from tabulate import tabulate
from tree_format import format_tree

import utils
from outputter import Outputter
from utils import rstrip_zeroes


class Lister(Outputter):
    def list_courses(self, courses, all=False, long=False):
        if all:
            display_courses = courses
        else:
            latest_term = max(course.enrollment_term_id for course in courses)
            display_courses = filter(lambda course: course.enrollment_term_id == latest_term, courses)

        if long:
            self.poutput(tabulate(map(utils.course_info_items, display_courses), tablefmt='plain'))
        else:
            self.poutput('\n'.join([utils.unique_course_code(c) for c in display_courses]))

    def list_assignments(self, course: Course, long=False, submissions=False, upcoming=False):
        if course is None:
            self.poutput('No course specified.')
            return False

        display_assignments = course.get_assignments()

        if upcoming:
            now = pytz.UTC.localize(datetime.now())
            display_assignments = filter(lambda assignment: assignment.due_at_date >= now, display_assignments)

        if long:
            if submissions:
                assignment_ids = map(lambda assignment: assignment.id, display_assignments)
                assignment_submissions = course.list_multiple_submissions(assignment_ids=assignment_ids)

                submissions_by_assignment = defaultdict(list)

                tabulated_submissions = utils.tabulate_dict(utils.submission_info_items, assignment_submissions)
                for submission, formatted in tabulated_submissions.items():
                    submissions_by_assignment[submission.assignment_id].append((formatted, []))

                tabulated_assignments = utils.tabulate_dict(utils.assignment_info_items, display_assignments)

                tree = (utils.unique_course_code(course), [(formatted, submissions_by_assignment[assignment.id]) for assignment, formatted in tabulated_assignments.items()])

                self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)))
            else:
                self.poutput(tabulate(map(utils.assignment_info_items, display_assignments), tablefmt='plain'))
        else:
            self.poutput('\n'.join([assignment.name for assignment in display_assignments]))

    def list_grades(self, course: Course, long=False):
        if course is None:
            self.poutput('No course specified.')
            return False

        display_assignments = course.get_assignments()
        submissions_by_assignment = utils.get_submissions_by_assignment(course, display_assignments)

        def tabulate_row(assignment):
            submission = next(submission for submission in submissions_by_assignment[assignment.id]
                         if hasattr(submission, 'score') and submission.score is not None)
            score = submission.score
            possible = assignment.points_possible
            fraction = f'{rstrip_zeroes(score)}/{rstrip_zeroes(possible)}'
            percentage = '{0:.0f}%'.format(score / possible * 100)
            if long:
                datetimestr = utils.compact_datetime(submission.submitted_at_date) if hasattr(submission, 'submitted_at_date') else ''
                return [submission.id, datetimestr, assignment.name, fraction, percentage]
            else:
                return [assignment.name, fraction, percentage]

        self.poutput(tabulate(map(tabulate_row, display_assignments), tablefmt='plain'))