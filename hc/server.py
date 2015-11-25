from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from . import config


class HcServer(LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        print('Got new client')
        self.factory.clients.append(self)
        #self.setRawMode()

    def connectionLost(self, reason):
        log.msg('Lost client')
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        log.msg('Server received: {0}'.format(line))
        self.factory.sr.cmd(line)


class HcServerFactory(Factory):
    protocol = HcServer
    clients = []
    sr = None

    def broadcast(self, msg):
        for client in self.clients:
            client.sendLine(msg)


def build():
    f = HcServerFactory()
    reactor.listenTCP(config.get('server_port'), f)

    return f
