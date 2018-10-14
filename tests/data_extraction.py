import argparse
import json
import os
import random
import shlex
import string
import sys

from canvasapi import Canvas

from clanvas import interfaces

USER_ACCOUNT_ID = 101
COURSE_CREATOR_ACCOUNT_ID = 501


def generate_canvas_uuid():
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
        range(40))


def get_course_data(canvas):
    return sorted([anonymize_user_course(course.attributes) for course in canvas.get_current_user().get_courses()],
                  key=lambda data: -data['enrollment_term_id'])


def anonymize_user_course(attributes):
    if attributes['enrollments'] and 'computed_current_score' in attributes['enrollments']:
        attributes['enrollments'][0]['computed_current_score'] = round(random.uniform(70, 100), 1)
    if attributes['enrollments'] and 'computed_final_score' in attributes['enrollments']:
        attributes['enrollments'][0]['computed_final_score'] = round(random.uniform(70, 100), 1)
    if attributes['enrollments'] and 'user_id' in attributes['enrollments']:
        attributes['enrollments'][0]['user_id'] = USER_ACCOUNT_ID
    if 'account_id' in attributes:
        attributes['account_id'] = COURSE_CREATOR_ACCOUNT_ID
    if 'uuid' in attributes:
        attributes['uuid'] = generate_canvas_uuid()

    del attributes['calendar']
    return attributes


def generate_course_fixture_json(courses_data):
    c = 1
    output = {}
    for course_data in courses_data:
        inner = {
            'path': f'courses/{course_data["id"]}',
            'method': 'GET',
            'status': 200,
            'body': course_data
        }
        output[f'course_{c}'] = inner
        c += 1
    return output


def get_user_profile(canvas):
    profile = canvas.get_current_user().get_profile()
    del profile['calendar']
    profile['id'] = USER_ACCOUNT_ID
    profile['lti_user_id'] = generate_canvas_uuid()
    return {'path': f'user/{USER_ACCOUNT_ID}/profile',
            'method': 'GET',
            'status': 200,
            'body': profile}


def get_course_fixtures(canvas):
    return generate_course_fixture_json(get_course_data(canvas))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate data from existing Canvas server.')
    parser.add_argument('action', help='name of a get_ACTION method to run with a canvas object')
    parser.add_argument('--output', '-o', default=None, help='file to output the extracted data to')
    parser.add_argument('--rcfile', '-r', help='get canvas credentials using a login command in the provided rcfile')

    args = parser.parse_args()
    fh = sys.stdout if args.output is None else open(os.path.expanduser(args.output), 'w')

    rcpath = os.path.expanduser(args.rcfile)
    if os.path.exists(rcpath):
        with open(rcpath, 'r') as rcfile:
            login_command = next(line for line in rcfile.readlines() if line.startswith('login '))
            login_args = interfaces.login_parser.parse_args(shlex.split(login_command)[1:])
            canvas = Canvas(login_args.url, login_args.token)

    if canvas is None:
        input_url = input('Please enter Canvas URL: ')
        input_token = input('Please enter Canvas token: ')
        canvas = Canvas(input_url, input_token)

    output = locals()[f'get_{args.action}'](canvas)

    json.dump(output, fh, indent=2)

