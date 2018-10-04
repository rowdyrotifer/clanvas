from enum import Enum


class Verbosity(Enum):
    OFF = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class Outputter:
    def __init__(self, printfn, verbosityfn):
        self.printfn = printfn
        self.verbosityfn = verbosityfn

    def check(self, verbosity):
        return self.verbosityfn().value >= verbosity.value

    def poutput(self, msg, end='\n', verbosity=Verbosity.NORMAL):
        if self.check(verbosity):
            self.printfn(msg + end)

    def poutput_normal(self, msg, end='\n'):
        self.poutput(msg, end, verbosity=Verbosity.NORMAL)

    def poutput_verbose(self, msg, end='\n'):
        self.poutput(msg, end, verbosity=Verbosity.VERBOSE)

    def poutput_debug(self, msg, end='\n'):
        self.poutput(msg, end, verbosity=Verbosity.DEBUG)


outputter: Outputter


def get_outputter() -> Outputter:
    """
    Gets the singleton outputter, which is set on instantiation
    of the Clanvas object.
    :return: the outputter instance that is associated the Clanvas object.
    """
    global outputter
    return outputter


def bind_outputter(printfn, verbosityfn):
    """
    Sets the global outputter variable accessible from get_outputter.
    :param printfn: a function that accepts a string to print out to user.
    :param verbosityfn: a function that provides a verbosity level.
    :return: None
    """
    global outputter
    outputter = Outputter(printfn, verbosityfn)
