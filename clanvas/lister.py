from collections import Sequence
from operator import itemgetter

from canvasapi.assignment import Assignment, AssignmentGroup
from canvasapi.exceptions import Unauthorized, CanvasException
from canvasapi.submission import Submission
from tree_format import format_tree

from .filters import latest_term_courses, future_assignments
from .outputter import Outputter
from .utils import *
from .utils import rstrip_zeroes


class Lister(Outputter):
    @staticmethod
    def course_info_items(c):
        return [c.course_code, c.id, c.term['name'] if hasattr(c, 'term') else '', c.name]

    def list_courses(self, courses, all=False, long=False):
        display_courses = courses if all else latest_term_courses(courses)

        if long:
            self.poutput(tabulate(map(Lister.course_info_items, display_courses), tablefmt='plain'))
        else:
            self.poutput('\n'.join([unique_course_code(c) for c in display_courses]))

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

                tabulated_submissions = tabulate_dict(submission_info_items, assignment_submissions)
                for submission, formatted in tabulated_submissions.items():
                    submissions_by_assignment[submission.assignment_id].append((formatted, []))

                tabulated_assignments = tabulate_dict(assignment_info_items, assignments)

                tree = (unique_course_code(course), [(formatted, submissions_by_assignment[assignment.id]) for assignment, formatted in tabulated_assignments.items()])

                self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)))
            else:
                self.poutput(tabulate(map(assignment_info_items, assignments), tablefmt='plain'))
        else:
            self.poutput('\n'.join([assignment.name for assignment in assignments]))

    def list_all_grades(self, courses: 'Sequence[Course]', long=False, groups=False, ungraded=False):
        for course in courses:
            self.list_grades(course, long=long, groups=groups, ungraded=ungraded)
            # course_info = ' '.join(str(item) for item in Lister.course_info_items(course))
            #
            # assignments = course.get_assignments()
            #
            # submissions_by_assignment = get_submissions_for_assignments(course, assignments)
            #
            # row_function = functools.partial(Lister.tabulate_grade_row, long=long, submissions_by_assignment=submissions_by_assignment)
            # rows = tabulate(map(row_function, assignments), tablefmt='plain').split('\n')
            #
            # tree = (course_info, [(row, []) for row in rows])
            #
            # self.poutput(format_tree(tree, format_node=itemgetter(0), get_children=itemgetter(1)), end='')

    @staticmethod
    def tabulate_grade_row(assignment, submission, long):
        possible = assignment.points_possible
        if submission is not None:
            score = submission.score
            fraction = f'{rstrip_zeroes(score)}/{rstrip_zeroes(possible)}'
            percentage = '{0:.0f}%'.format(score / possible * 100) if possible != 0 else 'N/A'
        else:
            fraction = f'?/{rstrip_zeroes(possible)}'
            percentage = ''

        if long:
            datetimestr = compact_datetime(submission.submitted_at_date) if hasattr(submission,
                                                                                          'submitted_at_date') else ''
            return [submission.id, datetimestr, assignment.name, fraction, percentage]
        else:
            return [assignment.name, fraction, percentage]

    @staticmethod
    def grades_tree(course: Course, groups=False, include_ungraded=False):
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

        if not groups:
            tree_items = [(assignment, submission) for assignment, submission in graded_assignment_submissions.items()
                          if include_ungraded or submission is not None]
        else:
            tree_items = []
            assignment_groups = course.list_assignment_groups()

            grouped_assignment_submission_pairs = {}
            for assignment, submission in graded_assignment_submissions.items():
                if include_ungraded or submission is not None:
                    if assignment.assignment_group_id not in grouped_assignment_submission_pairs:
                        grouped_assignment_submission_pairs[assignment.assignment_group_id] = []
                    grouped_assignment_submission_pairs[assignment.assignment_group_id].append((assignment, submission))

            for group in sorted(assignment_groups, key=lambda g: g.position):
                assignment_submission_pair = grouped_assignment_submission_pairs[group.id]\
                    if group.id in grouped_assignment_submission_pairs else []
                group_subtree = (group, assignment_submission_pair)
                tree_items.append(group_subtree)

        return course, tree_items

    def list_grades(self, course: Course, long=False, groups=False, ungraded=False):
        if course is None:
            self.poutput('No course specified.')
            return False

        try:
            tree = Lister.grades_tree(course, groups=groups, include_ungraded=ungraded)

            def format_node(node):
                item = node[0]
                if isinstance(item, Course):
                    return item.name
                elif isinstance(item, AssignmentGroup):
                    return item.name
                elif isinstance(item, Assignment):
                    assignment, submission = node
                    return ' '.join([str(x) for x in Lister.tabulate_grade_row(assignment, submission, long=long)])

            def get_children(node):
                if isinstance(node[1], Submission) or node[1] is None:
                    return []
                else:
                    return node[1]

            self.poutput(format_tree(tree, format_node=format_node, get_children=get_children), end='')
        except Unauthorized:
            self.poutput(f'{course.name}: Unauthorized')
        except CanvasException as e:
            self.poutput(f'{course.name}: {str(e)}')

    def list_announcements(self, course: Course, number=5, time=None):
        if course is None:
            self.poutput('No course specified.')
            return False

        return False
