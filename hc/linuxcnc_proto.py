import Queue

from twisted.python import log
from twisted.internet import reactor, task
from twisted.internet.defer import Deferred

import linuxcnc

from .command import Command
from .machine_proto import MachineTalk

MODES = {
    linuxcnc.MODE_MANUAL: 'manual',
    linuxcnc.MODE_AUTO: 'auto',
    linuxcnc.MODE_MDI: 'MDI',
}

INTERP_STATES = {
    linuxcnc.INTERP_IDLE: 'idle',
    linuxcnc.INTERP_READING: 'reading',
    linuxcnc.INTERP_PAUSED: 'paused',
    linuxcnc.INTERP_WAITING: 'paused',
}

def axisnumber(letter):
    return "xyzabcuvws".index(letter.lower())


class LinuxCNC(MachineTalk):
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
    #
    last_interp_state = None
    # our internal state machine tracking stat.interp_status
    # to know when interpreter is idle and we can send next command
    state = None

    def __init__(self, *args, **kwargs):
        super(LinuxCNC, self).__init__(*args, **kwargs)

    def connectionMade(self):
        log.msg('Machine {0} connected '.format(self))

        self.prio_queue = Queue.PriorityQueue()
        self.ack_queue = Queue.Queue()
        self.sent = []

        self.init_linuxcnc()

    def init_linuxcnc(self):
        self.stat = linuxcnc.stat()
        self.command = linuxcnc.command()
        self.error_channel = linuxcnc.error_channel()

        self.stat.poll()
        self.serial = self.stat.echo_serial_number
        self.cmd_serial = self.serial + 1
        self.error_channel.poll()

        self.last_interp_state = self.stat.interp_state

        self.poll_task = task.LoopingCall(self.poll_linuxcnc)
        self.poll_task.start(0.1)
        self.state = 'READY'

    def reset_interpreter(self):
        self.info('Resetting interpreter')
        self.command.reset_inrerpreter()

    def load_file(self, path):
        self.manual_mode()
        self.info('Loading {}'.format(path))
        self.command.program_open(path)

    def run(self):
        self.auto_mode()
        self.info('Running program')
        program_start_line = 0
        self.command.auto(linuxcnc.AUTO_RUN, program_start_line)

    def jog_start(self, axis, speed):
        self.manual_mode()
        self.command.jog(linuxcnc.JOG_CONTINUOUS, axis, speed)

    def jog_increment(self, axis, speed, distance):
        self.manual_mode()
        axis = axisnumber(axis)
        self.command.jog(linuxcnc.JOG_INCREMENT, axis, speed, distance)

    def jog_stop(self, axis):
        self.manual_mode()
        self.command.jog(linuxcnc.JOG_STOP, axis)

    def switch_mode(self, mode):
        m = MODES[mode]
        self.log('Switching to {} mode'.format(m))
        self.command.mode(mode)
        self.command.wait_complete()
        self.log('Switched to {} mode'.format(m))

    def auto_mode(self):
        self.switch_mode(linuxcnc.MODE_AUTO)

    def manual_mode(self):
        self.switch_mode(linuxcnc.MODE_MANUAL)

    def mdi_mode(self):
        self.switch_mode(linuxcnc.MODE_MDI)

    def poll_linuxcnc(self):
        self.stat.poll()
        inps = self.stat.interp_state

        if inps != self.last_interp_state:
            self.debug('Interpreter stage changed to {}'.format(INTERP_STATES[self.stat.interp_state]))
            self.last_interp_state = inps

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
        if error:
            kind, text = error
            if kind in (linuxcnc.NML_ERROR, linuxcnc.OPERATOR_ERROR):
                self.error(text)
            else:
                self.info(text)

    def handle_internal(self, cmd):
        res = 'unknown command'

        if cmd.raw.startswith('/ping'):
            res = '/pong'

        if cmd.raw.startswith('/load'):
            self.info('LOAD')
            self.load_file('/tmp/hc_test')
            res = 'ok'

        if cmd.raw.startswith('/run'):
            self.run()

        if cmd.raw.startswith('/jog'):
            self.jog_increment('x', 100, 1)
            res = 'ok'

        if cmd.raw.startswith('/python'):
            log.msg(cmd.raw)
            res = eval(cmd.raw.split(' ', 1)[1])

        if cmd.raw.startswith('/version'):
            res = '/version hacked_cnc beta'

        cmd.result = res
        reactor.callLater(0.1, cmd.d.callback, cmd)

    def cmd(self, cmd):
        """
        High level command handling
        """

        if not isinstance(cmd, Command):
            cmd = Command(cmd)

        if cmd.empty or cmd.comment:
            return cmd

        if cmd.internal:
            self.handle_internal(cmd)
            return cmd

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
            self.monitor.broadcast('> {0}'.format(cmd.text))

        if self.stat.interp_state == linuxcnc.INTERP_IDLE:
            if self.stat.task_mode != linuxcnc.MODE_MDI:
                self.mdi_mode()
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
