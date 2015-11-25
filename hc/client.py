from twisted.python import log
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ReconnectingClientFactory

from . import config


class HcClient(LineReceiver):
    delimiter = '\n'
    fwd = None

    def connectionMade(self):
        log.msg('Client connection made')
        self.factory.clientConnectionMade(self)

    def lineReceived(self, line):
        if self.fwd:
            self.fwd(line)
        else:
            print(line)

    def quit(self):
        self.factory.stopTrying()
        reactor.callLater(1, self.transport.loseConnection)


class HcClientFactory(ReconnectingClientFactory):
    protocol = HcClient

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
        log.msg('Client connection lost, reason {}'.format(reason))

        if self.disconnected_cb:
            self.disconnected_cb()

        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg('Client connection failed, reason {}'.format(reason))
        ReconnectingClientFactory.clientConnectionFailed(self,
                                                         connector, reason)


def build(connected_cb=None, disconnected_cb=None):
    f = HcClientFactory()
    f.connected_cb = connected_cb
    f.disconnected_cb = disconnected_cb

    reactor.connectTCP(config.get('server_host'),
                       config.get('server_port'), f)

    return f
