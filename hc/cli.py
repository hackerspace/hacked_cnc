import os
import sys
import logging
import datetime
import subprocess

from argh import ArghParser, named, arg, aliases
import argcomplete

from twisted.python import log
from twisted.internet import reactor

import hc
import hc.ui.probe.probe as probe
import hc.ui.monitor.monitor as qtmonitor

from hc import config
from hc.hacks import HackedSerialPort
from hc.machine_proto import SerialMachine

def path_completer(prefix, parsed_args, **kwargs):
    for o in get_metrics():
        yield "{}.{}".format(o.source.name, o.name)


def new_metric_completer(prefix, parsed_args, **kwargs):
    for o in get_metrics():
        yield "{}.".format(o.source.name)
        yield "{}.{}".format(o.source.name, o.name)


def source_completer(prefix, parsed_args, **kwargs):
    for o in get_sources():
        yield o.name


@named('server')
def server(stdio=False, linuxcnc=False):
    server = hc.server.build()
    monitor = hc.monitor.build_server()

    if linuxcnc:
        from hc.linuxcnc_proto import LinuxCNC
        from twisted.test.proto_helpers import FakeDatagramTransport
        proto = LinuxCNC(server)
    else:
        proto = SerialMachine(server)

    server.sr = proto
    monitor.sr = proto
    proto.monitor = monitor

    proto.ready_cb.addErrback(log.err)
    if stdio:
        stdio.StandardIO(proto)
    elif linuxcnc:
        transport = FakeDatagramTransport()
        proto.makeConnection(transport)
    else:
        HackedSerialPort(proto, config.get('port'), reactor,
                         baudrate=config.get('baudrate'))

    reactor.run()

@named('monitor')
def monitor(raw=False):

    def dump(data):
        print('"{}"'.format(data))

    def dump_raw(msg):
        print(msg)

    fact = hc.monitor.build_client()
    if raw:
        fact.fwd_raw = dump_raw
    else:
        fact.fwd = dump

    reactor.run()

@named('qtmonitor')
def uimon():
    os.chdir(os.path.dirname(qtmonitor.__file__))
    qtmonitor.main()

@named('pcb')
def uipcb():
    os.chdir(os.path.dirname(probe.__file__))
    probe.main()

# FIXME: drop after a while
@named('probe')
def uiprobe():
    os.chdir(os.path.dirname(probe.__file__))
    probe.main()

@named('shell')
def shell():
    import IPython
    IPython.embed()

def main():
    hc.setup()

    opt = "stdin_buffer_lines"
    buffer = 0
    buffering = False

    #if opt in CONFIG:
    #    buffering = True
    #    buffer = int(CONFIG[opt])

    if not sys.stdin.isatty():
        db = get_database()
        cbuffer = 0
        # FIXME: should handle g-code & stuff
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            path, value = line.split(' ', 1)
            if ' ' in value:  # timestamp present
                dt_in, value = value.split()
                dt = parse_timestamp(dt_in)
            else:
                dt = now()
            #print(o)
            cbuffer += 1

        sys.exit(0)

    #logging.basicConfig(level=logging.DEBUG)
    #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    parser = ArghParser()
    parser.add_commands([
        shell,
        server,
        monitor,
        uimon,
        uipcb,
        uiprobe,
    ])

    argcomplete.autocomplete(parser)

    try:
        parser.dispatch()
    except KeyboardInterrupt:
        sys.exit(1)
