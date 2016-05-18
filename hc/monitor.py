from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from . import config
from twisted.python import log
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ReconnectingClientFactory

from . import config


class HcMonitorClient(LineReceiver):
    delimiter = '\n'
    fwd = None

    def connectionMade(self):
        log.msg('MonitorClient connection made')
        self.factory.clientConnectionMade(self)

    def lineReceived(self, line):
        if self.fwd:
            self.fwd(line)
        else:
            print(line)

    def quit(self):
        self.factory.stopTrying()
        reactor.callLater(1, self.transport.loseConnection)


class HcMonitorClientFactory(ReconnectingClientFactory):
    protocol = HcMonitorClient

    def __init__(self):
        self.fwd = None
        self.proto = None
        self.connected_cb = None
        self.disconnected_cb = None

    def buildProtocol(self, addr):
        self.resetDelay()

        self.proto = self.protocol()
        self.proto.factory = self

        if self.fwd:
            self.proto.fwd = self.fwd

        return self.proto

    def clientConnectionMade(self, protocol):
        if self.connected_cb:
            self.connected_cb(protocol)

    def clientConnectionLost(self, connector, reason):
        log.msg('MonitorClient connection lost, reason {}'.format(reason))

        if self.disconnected_cb:
            self.disconnected_cb()

        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg('MonitorClient connection failed, reason {}'.format(reason))
        ReconnectingClientFactory.clientConnectionFailed(self,
                                                         connector, reason)


def build_client(connected_cb=None, disconnected_cb=None):
    f = HcMonitorClientFactory()
    f.connected_cb = connected_cb
    f.disconnected_cb = disconnected_cb

    reactor.connectTCP(config.get('monitor_host', 'localhost'),
                       config.get('monitor_port', 11010), f)

    return f

class HcMonitor(LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        print('Got new client')
        self.factory.clients.append(self)
        #self.setRawMode()

    def connectionLost(self, reason):
        log.msg('Lost client')
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        log.msg('Monitor received: {0}'.format(line))
        self.factory.sr.cmd(line)


class HcMonitorFactory(Factory):
    protocol = HcMonitor
    clients = []
    sr = None

    def broadcast(self, msg):
        for client in self.clients:
            client.sendLine(msg)


def build_server():
    f = HcMonitorFactory()
    reactor.listenTCP(config.get('monitor_port', 11010), f)

    return f
