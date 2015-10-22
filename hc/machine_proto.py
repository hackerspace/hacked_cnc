import Queue

from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.protocols.basic import LineReceiver

from .command import Command
from .util import trace


COLORED = True
DEBUG_SERIAL = False


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

    source = None
    source_fetch = None
    exit_when_done = False

    # maximum number of commands in queue waiting for 'ok' ack
    max_waiting_for_ack = 5
    # wrong ^^ we need to count character (256 characters for Smoothie)

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

    def connectionLost(self, reason):
        print('Serial connection lost, reason: ', reason)

    def cmd(self, cmd):
        """
        High level command handling
        """

        if not isinstance(cmd, Command):
            cmd = Command(cmd)

        if cmd.empty or cmd.comment:
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

            assert '\n' not in out

            cmd.pre_encoded = out

            self.line += 1

        self.prio_queue.put(cmd)
        self.try_tx()

        return cmd

    def try_tx(self):
        if self.prio_queue.empty():
            if self.source and self.source.depleted and self.exit_when_done:
                reactor.callLater(2, self.quit)
                return False

            return False

        if self.ack_queue.qsize() >= self.max_waiting_for_ack:
            return False

        try:
            cmd = self.prio_queue.get_nowait()
        except Queue.Empty:
            return False

        if self.serial_tx_verbose:
            print('> {0}'.format(cmd.text))
            self.srv.broadcast('> {0}\n'.format(cmd.text))

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
                self.try_tx()
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
            print('< {0}'.format(line))

        self.srv.broadcast('< {0}\n'.format(line))

        self.handle(line)

    def rawDataReceived(self, data):
        print('raw serial data:', data)

    def __str__(self):
        return "Generic Machine"

    def quit(self):
        reactor.callLater(1, reactor.stop)

    @trace
    def fetch_source(self, amount=100):
        if not self.source.hasdata:
            if self.source.depleted:
                self.source_fetch.stop()

            return

        lines = self.source.readlines(amount)
        for line in lines:
            self.cmd(line)

    @trace
    def feed_file(self, proto, fpath):
        self.source = GCodeSource(fpath)
        self.fetch_source(1000)
        self.source_fetch = task.LoopingCall(self.fetch_source)
        self.source_fetch.start(1)

        return proto


class GCodeSource(object):
    def __init__(self, fpath):
        self.file = open(fpath)
        self.depleted = False  # source depleted

    def readlines(self, num_lines):
        '''
        Read approximately num_lines
        '''
        if not self.file:
            return []

        lines = self.file.readlines(num_lines)
        if len(lines) == 0:
            self.file = None
            self.depleted = True
            return []

        return lines

    @property
    def hasdata(self):
        return self.file is not None
