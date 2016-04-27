from twisted.internet.defer import Deferred
from twisted.python import log


class Command(object):
    g = False
    m = False
    t = False
    special = False
    comment = False
    internal = False
    unknown = False

    acked = False
    empty = False
    raw = None
    normalized = None
    pre_encoded = None
    line = None

    d = None

    def ack(self, cmd):
        self.acked = True
        return cmd

    def __init__(self, cmd):
        self.raw = cmd
        self.d = Deferred()
        self.d.addCallback(self.ack)
        self.d.addErrback(log.err)

        cmd = cmd.strip()
        if not cmd:
            self.empty = True
            return

        self.normalized = cmd.upper()
        f = self.normalized[0]

        if f == 'G':  # standard g-code
            self.g = True
        elif f == 'M':  # RepRap command
            self.m = True
        elif f == 'T':  # select tool
            self.t = True
        elif f == '/':  # HC internal command
            self.internal = True
        elif f == 'N':  # line number, already encoded
            self.pre_encoded = self.raw
        elif f in [';', '(']:
            self.comment = True
        else:
            self.uknown = True

    def __cmp__(self, other):
        if self.special:
            if other.special:
                return 0
            return 1
        else:
            return cmp(self.line, other.line)

    @property
    def text(self):
        if self.pre_encoded:
            return self.pre_encoded
        elif self.special or self.empty:
            return self.raw
        else:
            return self.normalized

    def __str__(self):
        return self.text
