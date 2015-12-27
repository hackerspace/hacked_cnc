import random

from twisted.internet import task
from twisted.protocols.basic import LineReceiver

from . import log
from . import gcode

#from twisted.logger import Logger
# FIXME: update to ^^ when possible


class MockedPrinter(LineReceiver):
    delimiter = '\n'
    serial_rx_verbose = True
    serial_tx_verbose = True
    current_line = 0
    failcounter = 0
    warncounter = 0
    reserved = ['G', 'M', 'T', 'N']
    resend_next = False

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

    def info(self, msg):
        log.msg(msg)

    def fail(self, msg):
        self.failcounter += 1
        log.msg('Fail! {}'.format(msg))

    def warn(self, msg):
        self.warncounter += 1
        log.msg('Warning: {}'.format(msg))

    def request_resend(self):
        '''
        Request resend of current line
        '''

        ln = self.current_line
        self.cmd('rs N{}'.format(ln))

    def request_resend_on_next(self):
        self.resend_next = True

    def request_deep_resend(self):
        '''
        Of older command that we've previously acked. Tricky
        '''

        ln = self.current_line - random.randrange(0, 10)
        if ln < 0:
            ln = 0

        self.current_line = ln - 1
        self.cmd('rs {}'.format(ln))

    def lineReceived(self, line):
        if self.serial_rx_verbose:
            log.msg('M< {0}'.format(line))

        sl = line.strip().upper()
        if not sl:
            self.warn('Empty command received')
            return

        #log.msg('!!! {}'.format(sl[0]))
        if sl[0] in self.reserved:
            if self.resend_next:
                self.resend_next = False
                self.current_line += 1
                self.request_resend()
                return

            cmd, ln, crc = gcode.parse(sl)
            # FIXME: should compute checksum before parsing
            loc_crc = gcode.checksum('N{} {}'.format(ln, cmd))
            if loc_crc != crc:
                self.warn('Checksum mismatch r:{} vs l:{}'.format(crc, loc_crc))
                self.request_resend()
                return

            log.msg('CC', self.current_line, ln)
            # check for ln mismatches

            self.current_line += 1
            self.handle_line(sl)

        else:  # this is special command
            self.handle_special(sl)

    def handle_special(self, line):
        # trigger resend forcefully
        if 'RESEND' in line:
            self.request_resend_on_next()

    def handle_line(self, line):
        self.handle_command(line)

    def handle_command(self, line):
        if 'M110' in line:
            self.info('Resetting line number')
            self.current_line = 0

        if 'M114' in line:
            self.cmd('T:23.4 / 220.0 B:38.5 / 60.0')

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

        line = self.lines.pop(0)
        self.c_lines -= 1
        self.c_bytes -= len(line)
        log.msg("Executing {}".format(line))
        self.handle_command(line)

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
            self.fail('Firmware buffer overrun, max bytes exceeded')

        self.lines.append(line)

    def request_resend(self):
        self.c_lines = 0
        self.c_bytes = 0
        self.lines = []

        MockedPrinter.request_resend(self)
