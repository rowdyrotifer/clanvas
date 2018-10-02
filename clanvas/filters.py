from datetime import datetime, timedelta

import pytz


def latest_term_courses(courses):
    latest_term_int = max(course.enrollment_term_id for course in courses)
    return filter(lambda course: course.enrollment_term_id == latest_term_int, courses)


def future_assignments(assignments):
    now = pytz.UTC.localize(datetime.now())
    return filter(lambda assignment: assignment.due_at_date >= now, assignments)


def days_from_today(iterable, days, key):
    target = pytz.UTC.localize(datetime.now() - timedelta(days=days))
    return filter(lambda item: key(item) >= target, iterable)
