import tty
import termios

from twisted.internet.serialport import SerialPort


class HackedSerialPort(SerialPort):
    """
    SerialPort that doesn't flush input buffer
    on __init__ and instead reconfigures serial port
    """
    first_flush = True

    def flushInput(self):
        if self.first_flush:
            # don't flush, reconfigure instead
            self.reconfigure()
            self.first_flush = False
            return

        self._serial.flushInput()

    def reconfigure(self, state=True):
        """
        Allow HUPCL (hang up on close)
        VMIN, VTIME = 0
        """

        fd = self.fileno()

        orig_attr = termios.tcgetattr(fd)

        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = orig_attr

        cflag |= termios.HUPCL

        cc[termios.VMIN] = 0
        cc[termios.VTIME] = 0

        termios.tcsetattr(fd, termios.TCSANOW,
                          [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

class SerialBridge(object):
    def __init__(self, protoA, protoB):
        pass
