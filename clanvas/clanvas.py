import json

from canvasapi import Canvas


class Clanvas(object):

    def __init__(self, url, token):
        self.canvas = Canvas(url, token)
        self.current_class = None

    def welcome(self):
        profile = self.canvas.get_current_user().get_profile()
        print('Logged in as {:s} ({:s})'.format(profile['name'], profile['login_id']))

    def whoami(self, verbose=False):
        profile = self.canvas.get_current_user().user.get_profile()

        if not verbose:
            print(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            print('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))


    def list_courses(self):
        courses = self.canvas.get_courses()

        # sections = [section for course in courses for section in course.get_sections()]
        # print('\n'.join([section for field in sections]))



