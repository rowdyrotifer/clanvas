from canvasapi.exceptions import ResourceDoesNotExist
from html2text import html2text

from .utils import *


class Printer:
    def __init__(self, outputter):
        self.outputter = outputter

    def print_announcement(self, course: Course, ids):
        for announcement_id in ids:
            try:
                topic = course.get_discussion_topic(int(announcement_id))

                body = html2text('\n'.join(topic.message.splitlines())).strip()

                print_items = [topic.user_name,
                               long_datetime(topic.posted_at_date),
                               topic.title,
                               '',
                               body]

                self.outputter.poutput('\n'.join(print_items))
            except ResourceDoesNotExist:
                self.outputter.poutput(f'{str(announcement_id)}: no such announcement id for {unique_course_code(course)}')
