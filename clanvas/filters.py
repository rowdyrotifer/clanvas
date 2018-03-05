from datetime import datetime

import pytz


def latest_term_courses(courses):
    latest_term_int = max(course.enrollment_term_id for course in courses)
    return filter(lambda course: course.enrollment_term_id == latest_term_int, courses)


def future_assignments(assignments):
    now = pytz.UTC.localize(datetime.now())
    return filter(lambda assignment: assignment.due_at_date >= now, assignments)
