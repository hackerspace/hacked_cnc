from twisted.protocols.basic import LineReceiver


class MockedPrinter(LineReceiver):
    delimiter = '\n'
    serial_rx_verbose = not True
    serial_tx_verbose = not True

    def connectionMade(self):
        self.cmd('start')

    def cmd(self, cmd):
        if self.serial_tx_verbose:
            print('M> {0}'.format(cmd))

        self.transport.write(cmd)
        self.transport.write('\n')

    def ack(self):
        if self.serial_tx_verbose:
            print('M> ok')

        self.transport.write('ok\n')

    def lineReceived(self, line):
        if self.serial_rx_verbose:
            print('M< {0}'.format(line))

        self.handle(line)

    def handle(self, line):
        sl = line.strip()
        if not sl:
            return

        if line == 'M110':
            self.cmd('Res')

        if 'M114' in line:
            self.cmd('Temp lala')

        self.ack()


class BufferedMockedPrinter(LineReceiver):
    delimiter = '\n'
    serial_rx_verbose = True
    serial_tx_verbose = True

    def connectionMade(self):
        self.cmd('start')

    def cmd(self, cmd):
        if self.serial_tx_verbose:
            print('M> {0}'.format(cmd))

        self.transport.write(cmd)
        self.transport.write('\n')

    def ack(self):
        if self.serial_tx_verbose:
            print('M> ok')

        self.transport.write('ok\n')

    def lineReceived(self, line):
        if self.serial_rx_verbose:
            print('M< {0}'.format(line))

        self.handle(line)

    def handle(self, line):
        sl = line.strip()
        if not sl:
            return

        if line == 'M110':
            self.cmd('Res')

        if line == 'M114':
            self.cmd('Temp lala')

        self.ack()
