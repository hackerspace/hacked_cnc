import random

from twisted.internet import task
from twisted.protocols.basic import LineReceiver

from . import log

#from twisted.logger import Logger
# FIXME: update to ^^ when possible


class MockedPrinter(LineReceiver):
    delimiter = '\n'
    serial_rx_verbose = True
    serial_tx_verbose = True
    current_line = 0

    def connectionMade(self):
        self.cmd('start')

    def cmd(self, cmd):
        if self.serial_tx_verbose:
            log.msg('M> {0}'.format(cmd))

        self.transport.write(cmd)
        self.transport.write('\n')

    def ack(self):
        if self.serial_tx_verbose:
            log.msg('M> ok')

        self.transport.write('ok\n')

    def fail(self, msg):
        log.msg('Fail! {}'.format(msg))

    def request_resend(self):
        ln = self.current_line - random.randrange(0, 10)
        if ln < 0:
            ln = 0

        self.current_line = ln - 1
        self.cmd('rs {}'.format(ln))

    def lineReceived(self, line):
        self.current_line += 1
        if self.serial_rx_verbose:
            log.msg('M< {0}'.format(line))

        self.handle_line(line)

    def handle_line(self, line):
        self.handle(line)

    def handle(self, line):
        sl = line.strip()
        if not sl:
            return

        if line == 'M110':
            self.cmd('Res')

        if 'M114' in line:
            self.cmd('Temp lala')

        if 'resend' in line:
            self.request_resend()

        self.ack()


class BufferedMockedPrinter(MockedPrinter):
    max_lines = 10
    max_bytes = 256
    interval = 1

    def __init__(self):
        self.lines = []
        self.c_lines = 0
        self.c_bytes = 0
        self.loop = task.LoopingCall(self.run)
        self.loop.start(self.interval)

    def run(self):
        if self.c_lines == 0:
            return

        line = self.lines.pop()
        self.c_lines -= 1
        self.c_bytes -= len(line)
        log.msg("Executing {}".format(line))
        self.handle(line)

    def buffer_stat(self):
        log.msg("{}/{}, {}/{}".format(self.c_lines, self.max_lines,
                                      self.c_bytes, self.max_bytes))



    def handle_line(self, line):
        self.c_lines += 1
        self.c_bytes += len(line)
        self.buffer_stat()

        if self.c_lines >= self.max_lines:
            self.fail('Firmware buffer overrun, max lines exceeded')

        if self.c_bytes >= self.max_bytes:
            self.fail('Firmware buffer overrun, max lines exceeded')

        self.lines.append(line)

    def request_resend(self):
        self.c_lines = 0
        self.c_bytes = 0
        self.lines = []

        MockedPrinter.request_resend(self)
