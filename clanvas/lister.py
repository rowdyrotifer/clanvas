from collections import defaultdict, Sequence
from operator import itemgetter

import functools
from canvasapi.course import Course
from tabulate import tabulate
from tree_format import format_tree

import utils
from filters import latest_term_courses, future_assignments
from outputter import Outputter
from utils import rstrip_zeroes


class Lister(Outputter):
    @staticmethod
    def course_info_items(c):
        return [c.course_code, c.id, c.term['name'] if hasattr(c, 'term') else '', c.name]

    def list_courses(self, courses, all=False, long=False):
        display_courses = courses if all else latest_term_courses(courses)

        if long:
            self.poutput(tabulate(map(Lister.course_info_items, display_courses), tablefmt='plain'))
        else:
            self.poutput('\n'.join([utils.unique_course_code(c) for c in display_courses]))

    def list_assignments(self, course: Course, long=False, submissions=False, upcoming=False):
        if course is None:
            self.poutput('No course specified.')
            return False

        assignments = course.get_assignments()

        if upcoming:
            assignments = future_assignments(assignments)

        if long:
            if submissions:
                assignment_ids = map(lambda assignment: assignment.id, assignments)
                assignment_submissions = course.list_multiple_submissions(assignment_ids=assignment_ids)

                submissions_by_assignment = defaultdict(list)

                tabulated_submissions = utils.tabulate_dict(utils.submission_info_items, assignment_submissions)
                for submission, formatted in tabulated_submissions.items():
                    submissions_by_assignment[submission.assignment_id].append((formatted, []))

                tabulated_assignments = utils.tabulate_dict(utils.assignment_info_items, assignments)

                tree = (utils.unique_course_code(course), [(formatted, submissions_by_assignment[assignment.id]) for assignment, formatted in tabulated_assignments.items()])

                self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)))
            else:
                self.poutput(tabulate(map(utils.assignment_info_items, assignments), tablefmt='plain'))
        else:
            self.poutput('\n'.join([assignment.name for assignment in assignments]))

    def list_all_grades(self, courses: 'Sequence[Course]', long=False):
        for course in courses:
            course_info = ' '.join(str(item) for item in Lister.course_info_items(course))

            assignments = course.get_assignments()

            submissions_by_assignment = utils.get_submissions_for_assignments(course, assignments)

            row_function = functools.partial(Lister.tabulate_grade_row, long=long, submissions_by_assignment=submissions_by_assignment)
            rows = tabulate(map(row_function, assignments), tablefmt='plain').split('\n')

            tree = (course_info, [(row, []) for row in rows])

            self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)), end='')


    @staticmethod
    def tabulate_grade_row(assignment, submission, long):
        score = submission.score
        possible = assignment.points_possible
        fraction = f'{rstrip_zeroes(score)}/{rstrip_zeroes(possible)}'
        percentage = '{0:.0f}%'.format(score / possible * 100)
        if long:
            datetimestr = utils.compact_datetime(submission.submitted_at_date) if hasattr(submission,
                                                                                          'submitted_at_date') else ''
            return [submission.id, datetimestr, assignment.name, fraction, percentage]
        else:
            return [assignment.name, fraction, percentage]

    def list_grades(self, course: Course, long=False):
        if course is None:
            self.poutput('No course specified.')
            return False

        assignments = course.get_assignments()
        submissions_by_assignment = utils.get_submissions_for_assignments(course, assignments)

        def graded_submission(assignment):
            if assignment.id in submissions_by_assignment:
                submissions = submissions_by_assignment[assignment.id]
                submission = next((s for s in submissions if hasattr(s, 'grade') and s.grade is not None), None)
                if submission is not None:
                    return submission
            return None

        graded_assignment_submissions = {assignment:graded_submission(assignment) for assignment in assignments}

        table = [Lister.tabulate_grade_row(long=long, assignment=assignment, submission=submission)
                 for assignment, submission in graded_assignment_submissions.items() if submission is not None]
        self.poutput(tabulate(table, tablefmt='plain'))

        return False

    def list_announcements(self, course: Course, number=5, time=None):
        if course is None:
            self.poutput('No course specified.')
            return False

        return False
