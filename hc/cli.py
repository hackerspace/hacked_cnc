import os
import sys
import logging
import datetime
import subprocess

from argh import ArghParser, named, arg, aliases
import argcomplete

from twisted.internet import reactor

import hc
import hc.ui.probe.probe as probe
import hc.ui.monitor.monitor as qtmonitor


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

@named('monitor')
def monitor(raw=False):
    hc.setup()

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

@named('probe')
def uiprobe():
    os.chdir(os.path.dirname(probe.__file__))
    probe.main()

@named('shell')
def shell():
    import IPython
    IPython.embed()

def main():
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
        monitor,
        uimon,
        uiprobe,
    ])

    argcomplete.autocomplete(parser)

    try:
        parser.dispatch()
    except KeyboardInterrupt:
        sys.exit(1)
