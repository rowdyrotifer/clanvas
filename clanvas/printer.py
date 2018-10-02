from html2text import html2text

from .utils import *


class Printer:
    def __init__(self, outputter):
        self.outputter = outputter

    def print_announcement(self, course: Course, id):
        if course is None:
            self.outputter.poutput('No course specified.')
            return False

        topic = course.get_discussion_topic(int(id[0]))

        body = html2text('\n'.join(topic.message.splitlines())).strip()

        print_items = [topic.user_name,
                       long_datetime(topic.posted_at_date),
                       topic.title,
                       '',
                       body]

        self.outputter.poutput('\n'.join(print_items))

        return False
