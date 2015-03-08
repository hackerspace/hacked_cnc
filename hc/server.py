from twisted.python import log
from twisted.internet.protocol import Factory, ClientFactory
from twisted.protocols.basic import LineReceiver


class MonitorServer(LineReceiver):
    delimiter = '\n'

    def connectionMade(self):
        print('got new client')
        self.factory.clients.append(self)
        #self.setRawMode()

    def connectionLost(self, reason):
        log.msg('lost client')
        self.factory.clients.remove(self)

    def lineReceived(self, line):
        print 'recieved: {0}'.format(line)
        self.factory.sr.cmd(line)


class MonitorFactory(Factory):
    protocol = MonitorServer
    clients = []
    sr = None

    def broadcast(self, msg):
        for client in self.clients:
            client.sendLine(msg)


class MonitorClient(LineReceiver):
    delimiter = '\n'
    fwd = None

    def lineReceived(self, line):
        if self.fwd:
            self.fwd(line)
        else:
            print(line)


class MonitorClientFactory(ClientFactory):
    protocol = MonitorClient
    fwd = None
    cp = None

    def buildProtocol(self, addr):
        proto = self.protocol()
        self.cp.p = proto
        if self.fwd:
            proto.fwd = self.fwd

        return proto
