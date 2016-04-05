from twisted.python import log
from twisted.internet import reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from . import config
from . import util


class HcServer(LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        print('Got new client')
        self.transport.setTcpNoDelay(True)
        self.transport.setTcpKeepAlive(True)
        self.factory.clients.append(self)
        #self.setRawMode()

    def connectionLost(self, reason):
        log.msg('Lost client')
        self.factory.clients.remove(self)

    def ack(self, cmd, idx):
        em = util.enc_msg(cmd.result, idx)
        log.msg('Server acking: {0}'.format(em))
        self.sendLine(em)

    def lineReceived(self, line):
        line = line.strip()
        if not line:
            return

        log.msg('Server received: {0}'.format(line))

        (idx, msg) = util.dec_msg(line)

        cmd = self.factory.sr.cmd(msg)
        if cmd:
            cmd.d.addCallback(self.ack, idx)


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
