from html2text import html2text

from .utils import *


class Printer:
    def __init__(self, outputter):
        self.outputter = outputter

    def print_announcement(self, course: Course, ids):
        if course is None:
            self.outputter.poutput('No course specified.')
            return False

        for announcement_id in ids:
            topic = course.get_discussion_topic(int(announcement_id))

            body = html2text('\n'.join(topic.message.splitlines())).strip()

            print_items = [topic.user_name,
                           long_datetime(topic.posted_at_date),
                           topic.title,
                           '',
                           body]

            self.outputter.poutput('\n'.join(print_items))

        return True
