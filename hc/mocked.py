import math
import random

import collections

from twisted.internet import task
from twisted.protocols.basic import LineReceiver

from . import config, log, gcode, parse, vars

#from twisted.logger import Logger
# FIXME: update to ^^ when possible


class MockedPrinter(LineReceiver, object):
    delimiter = '\n'
    serial_rx_verbose = True
    serial_tx_verbose = True
    current_line = 0
    failcounter = 0
    warncounter = 0

    resend_next = False

    temploopinterval = 1

    temps = collections.OrderedDict()
    temp_designators = vars.temp_designators

    axes = collections.OrderedDict()
    axes_designators = vars.axes_designators

    def __init__(self):
        super(MockedPrinter, self).__init__()

        for d in self.temp_designators:
            # current, target, power
            self.temps[d] = [0.0, 0.0, 0]

        for d in self.axes_designators:
            self.axes[d] = 0.0

        self.temploop = task.LoopingCall(self.update_temperature)
        self.temploop.start(self.temploopinterval)

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

        if sl[0] in vars.gcode_reserved:
            if self.resend_next:
                self.resend_next = False
                self.current_line += 1
                self.request_resend()
                return

            cmd, ln, crc = gcode.parse(sl)
            # FIXME: should compute checksum before parsing
            if ln and crc:
                loc_crc = gcode.checksum('N{} {}'.format(ln, cmd))
                if loc_crc != crc:
                    self.warn('Checksum mismatch r:{} vs l:{}'.format(crc, loc_crc))
                    self.request_resend()
                    return

            log.msg('CC', self.current_line, ln)
            # FIXME: check for ln mismatches

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
        if 'G0' in line or 'G1' in line:
            for axis, val in parse.axes(line).items():
                self.axes[axis] = val

        if 'G30' in line:
            #z, c = self.zprobe()
            z, c = -1.14, 43000

            #z += self.axes['X'] / 10 + self.axes['Y'] / 10
            z += math.sin(self.axes['X']) + math.cos(self.axes['Y'])

            self.cmd('Z:{:.4f} C:{}'.format(z, c))

        if 'G38.2' in line or 'G38.3' in line:
            succ = 1
            x = self.axes['X']
            y = self.axes['Y']
            z = -1.0
            z += math.sin(x) + math.cos(y)
            self.cmd('[PRB:{:1.3f},{:1.3f},{:1.3f}:{}]'.format(x, y, z, succ))

        if 'M110' in line:
            self.info('Resetting line number')
            self.current_line = 0

        if 'M104' in line:
            x = parse.params(line)
            if 'S' in x:
                self.temps['T'][1] = x['S']

        if 'M140' in line:
            x = parse.params(line)
            if 'S' in x:
                self.temps['B'][1] = x['S']
                return

            self.warn('Unable to parse temp from {}'.format(line))

        if 'M105' in line:
            # ok T:25.0 /0.0 @0 T:24.4 /0.0 @0
            temp_template = '{}:{:.2f} /{:.2f} @{} '
            out = ''
            for designator, t in self.temps.items():
                current, target, power = t
                out += temp_template.format(designator, current, target, power)
            self.cmd('ok ' + out[:-1])
            return  # don't send another ack

        if 'M114' in line:
            # ok C: X:0.000 Y:0.000 Z:0.000 A:192.031 B:192.031 C:192.031  E:0.000
            pos_template = '{}:{:.3f} '
            out = ''
            for designator, pos in self.axes.items():
                out += pos_template.format(designator, pos)
            self.cmd(out[:-1])

        if 'M119' in line:
            # min_x:0 min_y:0  Probe: 0
            self.cmd('min_x:0 min_y:0  Probe: 0')

        if 'MULTILINE' in line:
            for i in range(10):
                self.cmd('Line {}'.format(i))

        self.ack()

    def update_temperature(self):
        for designator, t in self.temps.items():
            current, target, power = t

            power = random.randrange(0, 255)
            temp = random.randrange(0, 10)

            if current <= target:
                current += temp
            elif current > target:
                current -= temp

            self.temps[designator] = [current, target, power]


class BufferedMockedPrinter(MockedPrinter):
    max_lines = 10
    max_bytes = 256
    interval = config.get('interval', 0.5)

    def __init__(self):
        super(BufferedMockedPrinter, self).__init__()

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
