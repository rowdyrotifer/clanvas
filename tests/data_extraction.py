import random
import string

USER_ACCOUNT_ID = 101
COURSE_CREATOR_ACCOUNT_ID = 501


def generate_canvas_uuid():
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
        range(40))


def generate_course_fixture_json(canvas):
    courses = canvas.get_current_user().get_courses()

    def anonymize(attributes):
        attributes['enrollments'][0]['computed_current_score'] = round(random.uniform(70, 100), 1)
        attributes['enrollments'][0]['computed_final_score'] = round(random.uniform(70, 100), 1)
        attributes['enrollments'][0]['user_id'] = USER_ACCOUNT_ID
        attributes['account_id'] = COURSE_CREATOR_ACCOUNT_ID
        attributes['uuid'] = generate_canvas_uuid()

        del attributes['calendar']
        return attributes

    return [anonymize(course.attributes) for course in courses]


if __name__ == '__main__':
    pass
