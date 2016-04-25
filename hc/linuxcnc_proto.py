import Queue

from twisted.python import log
from twisted.internet import reactor, task
from twisted.internet.defer import Deferred
from twisted.protocols.basic import LineReceiver

import linuxcnc

from . import config
from .command import Command


class LinuxCNC(LineReceiver):
    line = 0
    ack_queue = None
    prio_queue = None
    sent = None
    resend_counter = 0

    ready_cb = Deferred()

    verbose = True

    exit_when_done = False

    max_waiting_for_ack = 1

    command_result_candidate = []

    # linuxcnc
    poll_task = None
    stat = None
    last_line = None
    # our internal state machine tracking stat.interp_status
    # to know when interpreter is idle and we can send next command
    state = None

    def __init__(self, srv):
        self.srv = srv
        self.command = linuxcnc.command()

    def connectionMade(self):
        log.msg('Machine {0} connected '.format(self))

        self.prio_queue = Queue.PriorityQueue()
        self.ack_queue = Queue.Queue()
        self.sent = []

        self.init_linuxcnc()

    def init_linuxcnc(self):
        self.stat = linuxcnc.stat()
        self.error_channel = linuxcnc.error_channel()

        self.stat.poll()
        self.serial = self.stat.echo_serial_number
        self.cmd_serial = self.serial + 1
        self.error_channel.poll()

        self.poll_task = task.LoopingCall(self.poll_linuxcnc)
        self.poll_task.start(0.1)
        self.state = 'READY'

    def poll_linuxcnc(self):
        self.stat.poll()
        if self.state == 'BUSY' and self.stat.interp_state == linuxcnc.INTERP_IDLE:
            log.msg('now idle again')
            self.state = 'IDLE'

            self.serial = self.stat.echo_serial_number
            log.msg('Serial {}'.format(self.serial))

            cmd = self.ack_queue.get_nowait()
            if cmd.line <= self.serial:
                cmd.result = 'ok'
                if cmd.text.startswith('G38.2'):
                    if self.stat.probe_tripped:
                        cmd.result = 'Z: {}'.format(self.stat.probed_position[2])
                    else:
                        cmd.result = 'probe not tripped'

                reactor.callLater(0.1, cmd.d.callback, cmd)
                log.msg('acked cmd: {}'.format(cmd.text))
                self.try_tx()
            else:
                log.msg('not reached cmd: {}'.format(cmd.line))
                self.ack_queue.put(cmd)

        error = self.error_channel.poll()
        # FIXME: better error handling
        if error:
            log.msg('error')
            self.srv.broadcast('err!')

    def connectionLost(self, reason):
        log.msg('Serial connection lost, reason: ', reason)

    def fatal(self, msg):
        log.msg('Fatal error: {}'.format(msg))
        # FIXME: what now?

    def cmd(self, cmd):
        """
        High level command handling
        """

        if not isinstance(cmd, Command):
            cmd = Command(cmd)

        if cmd.empty or cmd.comment:
            return

        cmd.line = self.cmd_serial
        self.cmd_serial += 1
        log.msg('adding {}'.format(cmd.line))

        self.prio_queue.put(cmd)
        self.try_tx()

        return cmd

    def try_tx(self):
        if self.prio_queue.empty():
            if self.exit_when_done:
                reactor.callLater(2, self.quit)
                return False

            return False

        if self.ack_queue.qsize() >= self.max_waiting_for_ack:
            return False

        try:
            cmd = self.prio_queue.get_nowait()
        except Queue.Empty:
            return False

        if self.verbose:
            log.msg('> {0}'.format(cmd.text))
            self.monitor.broadcast('> {0}\n'.format(cmd.text))

        if self.stat.interp_state == linuxcnc.INTERP_IDLE:
            self.command.mdi(cmd.text)
            self.state = 'BUSY'
        else:
            log.msg('error, interpret busy')

        if not cmd.special:
            self.ack_queue.put(cmd)

        if not self.prio_queue.empty():
            self.try_tx()

        return True

    def buffer_stat(self):
        log.msg('ACK Queue: {0}'.format(self.ack_queue.qsize()))
        log.msg('PRIO Queue: {0}'.format(self.prio_queue.qsize()))
        log.msg('Sent Queue: {0}'.format(len(self.sent)))

    def lineReceived(self, line):
        if self.verbose:
            log.msg('< {0}'.format(line))
            log.msg('ignoring')

    def rawDataReceived(self, data):
        log.msg('raw serial data:', data)

    def __str__(self):
        return "LinuxCNC Machine"

    def quit(self):
        reactor.callLater(1, reactor.stop)
