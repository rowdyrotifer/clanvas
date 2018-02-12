import os
from urllib.parse import urlparse

from canvasapi import Canvas
from tabulate import tabulate

from colorama import Fore
from colorama import Style

class Clanvas(object):

    def __init__(self, url, token):
        self.url = url
        self.host = urlparse(url).netloc
        self.canvas = Canvas(url, token)

        # Cacheable
        self.__courses = None
        self.current_user_profile = None

        self.current_course = None
        self.home = os.path.expanduser("~")
        self.current_directory = self.home

    prompt_string = Fore.LIGHTGREEN_EX + '{login_id}@{host}' + Style.RESET_ALL + ':' + Fore.MAGENTA + '{pwc}' + Style.RESET_ALL + ':' + Fore.CYAN + '{pwd} ' + Style.RESET_ALL + '$ '

    def get_prompt(self):
        login_id = self.__current_user_profile()['login_id']
        host = self.host
        pwc = self.current_course.course_code.replace(' ', '') if self.current_course is not None else '~'
        pwd = self.current_directory.replace(self.home, '~')
        return self.prompt_string.format(
            login_id=login_id,
            host=host,
            pwc=pwc,
            pwd=pwd
        )

    def get_courses(self, invalidate=False):
        if self.__courses is None or invalidate:
            sorter = lambda course: (-course.enrollment_term_id, course.name)
            self.__courses = sorted(self.canvas.get_current_user().get_courses(), key=sorter)
            # self.__update_courses_autocomplete_keys()

        return self.__courses
    #
    # def __update_courses_autocomplete_keys(self):
    #     keys = {}
    #     for course in self.courses:
    #         keys[course.]


    def __current_user_profile(self, invalidate=False):
        if self.current_user_profile is None or invalidate:
            self.current_user_profile = self.canvas.get_current_user().get_profile()

        return self.current_user_profile

    def login_info(self):
        profile = self.__current_user_profile()
        print('Logged in as {:s} ({:s})'.format(profile['name'], profile['login_id']))

    def whoami(self, verbose=False):
        profile = self.canvas.get_current_user().get_profile()

        if not verbose:
            print(profile['name'] + ' (' + profile['login_id'] + ')')
        else:
            verbose_fields = ['name', 'short_name', 'login_id', 'primary_email', 'id', 'time_zone']
            print('\n'.join([field + ': ' + str(profile[field]) for field in verbose_fields]))

    list_long_row = lambda course: [course.course_code, course.start_at_date.strftime("%b %y") if hasattr(course, 'start_at_date') else '', course.name, course.id]

    def list_courses(self, all=False, long=False, invalidate=False):
        courses = self.get_courses(invalidate)

        if all:
            display_courses = courses
        else:
            latest_term = max(course.enrollment_term_id for course in courses)
            filterer = lambda course: course.enrollment_term_id == latest_term
            display_courses = filter(filterer, courses)

        if long:
            print(tabulate([Clanvas.list_long_row(course) for course in display_courses], tablefmt='plain'))
        else:
            print('\n'.join([course.course_code for course in display_courses]))

    def change_course(self, course_id):
        self.current_course = next(course for course in self.get_courses() if course.id == course_id)


