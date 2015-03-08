import math

import Queue

from twisted.python import log
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.task import LoopingCall
from twisted.protocols.basic import LineReceiver

from hc import server
from hc.hacks import HackedSerialPort
from hc.mocked import MockedPrinter
from hc.util import trace

from fabulous import color


COLORED = True
DEBUG_SERIAL = False



class Command(object):
    g = False
    m = False
    t = False
    special = False

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

        if not cmd.strip():
            self.empty = True

        self.normalized = cmd.upper()
        f = self.normalized[0]

        if f == 'G':  # standard g-code
            self.g = True
        elif f == 'M':  # RepRap command
            self.m = True
        elif f == 'T':  # select tool
            self.t = True
        else:
            self.special = True

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


class MachineTalk(LineReceiver):
    delimiter = '\n'
    test_gcode = 'M114'
    serial_rx_verbose = True
    serial_tx_verbose = True
    numbered = True
    checksummed = True
    line = 0
    ack_queue = None
    prio_queue = None
    sent = None
    reset_line_numbering = True

    ready_cb = Deferred()

    max_waiting_for_ack = 10

    def __init__(self, srv):
        self.srv = srv

    def connectionMade(self):
        print('Machine {0} connected '.format(self))
        if DEBUG_SERIAL:
            self.setRawMode()

        self.prio_queue = Queue.PriorityQueue()
        self.ack_queue = Queue.Queue()
        self.sent = []

        if self.reset_line_numbering:
            self.cmd('M110 N0')

        self.test_connection()

    def connectionLost(self):
        print('Serial connection lost')

    def cmd(self, cmd):
        """
        High level command handling
        """

        if not isinstance(cmd, Command):
            cmd = Command(cmd)

        if cmd.empty:
            return

        if not (cmd.special or cmd.pre_encoded):  # apply Numbering and CRC for normal commands
            out = ''

            if self.numbered:
                out += 'N{0} '.format(self.line)

            out += cmd.text

            if self.checksummed:
                # compute checksum from line number + command
                out += '*{0}'.format(self.checksum(out))

            cmd.line = self.line
            cmd.pre_encoded = out

            self.line += 1

        self.prio_queue.put(cmd)
        self.try_tx()

        return cmd

        #if COLORED:
        #    out = color.red(cmd.text)
        #print(out)

    def try_tx(self):
        if (self.prio_queue.empty()
                or self.ack_queue.qsize() >= self.max_waiting_for_ack):

            return False

        try:
            cmd = self.prio_queue.get_nowait()
        except Queue.Empty:
            return False

        if self.serial_tx_verbose:
            cline = cmd.text
            if COLORED:
                cline = color.red(cline)

            print('> {0}'.format(cline))

        self.transport.write(cmd.text)
        self.transport.write('\n')

        if not cmd.special:
            self.ack_queue.put(cmd)

        if not self.prio_queue.empty():
            self.try_tx()

        return True

    def buffer_stat(self):
        print('ACK Queue: {0}'.format(self.ack_queue.qsize()))
        print('PRIO Queue: {0}'.format(self.prio_queue.qsize()))
        print('Sent Queue: {0}'.format(len(self.sent)))

    def checksum(self, cmd):
        return reduce(lambda x, y: x ^ y, map(ord, cmd))

    def handle(self, line):
        sl = line.strip()

        if sl.startswith('ok'):
            try:
                cmd = self.ack_queue.get_nowait()
                reactor.callLater(0.1, cmd.d.callback, cmd)
                print 'acked cmd:', cmd.text
                self.sent.append(cmd)
            except Queue.Empty:
                # more ok's than commands we've sent
                print 'more acks'
                pass

        #if sl.startswith('rs')

        if self.connection_test:
            self.handle_connection_test(sl)

        if sl == 'Smoothie':
            print('Smoothie detected')

    def test_connection(self):
        self.connection_test = True
        self.cmd(self.test_gcode)

    def test_gcode_expected(self, line):
        return 'ok' in line

    def handle_connection_test(self, line):
        print repr(line)
        if self.test_gcode_expected(line):
            print('Connection test passed')
            self.connection_test = False
            self.healthy = True

            self.ready_cb.callback(self)

    def lineReceived(self, line):

        if self.serial_rx_verbose:
            cline = line
            if COLORED:
                cline = color.green(cline)
            print('< {0}'.format(cline))

        self.srv.broadcast(line)

        self.handle(line)

    def rawDataReceived(self, data):
        print('raw serial data:', data)

    def __str__(self):
        return "Generic Machine"

    def quit(self):
        reactor.callLater(1, reactor.stop)


if __name__ == '__main__':
    #MockedPrinter(proto)

    from twisted.internet import task

    @trace
    def handle_temp(cmd):
        print 'TEMP'
        print cmd

    @trace
    def probe(proto):
        c = proto.cmd('M114')
        c.d.addCallback(handle_temp)

    def bfs(proto):
        proto.buffer_stat()

    tcpfactory = server.MonitorFactory()
    reactor.listenTCP(8000, tcpfactory)

    proto = MachineTalk(tcpfactory)
    tcpfactory.sr = proto
    proto.ready_cb.addCallback(probe)
    proto.ready_cb.addErrback(log.err)
    HackedSerialPort(proto, '/dev/ttyACM0', reactor, baudrate='250000')

    """
    bs = task.LoopingCall(bfs)
    bs.start(1.3)
    """

    reactor.run()

# > N3 N2 M114*37*86
# triggers real rs
