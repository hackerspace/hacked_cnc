#!/usr/bin/python2

import sys

from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog
from PyQt5.uic import loadUi
from PyQt5.QtNetwork import QTcpSocket, QAbstractSocket


class Main(QMainWindow):
    def __init__(self, *args):
        super(Main, self).__init__(*args)

        loadUi('mainwindow.ui', self)

        self.host.setText("localhost")
        self.port.setText("11010")
        self.prompt.setText("M114")

        self.conn = QTcpSocket(self)
        self.conn.readyRead.connect(self.readSocket)
        self.conn.error.connect(self.socketError)
        self.conn.connected.connect(self.socketConnect)
        self.conn.disconnected.connect(self.socketDisconnect)

        self.connected = False

        self.actionSave.triggered.connect(self.save)

        self.prompt.setFocus()

        self.do_connect()

    def append(self, text):
        self.text.append(text)

        if self.autoscroll.isChecked():
            c = self.text.textCursor()
            c.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.text.setTextCursor(c)

    def readSocket(self):
        r = self.conn.readAll()
        if r:
            r = str(r).strip()
            for chunk in r.splitlines():
                if chunk:
                    if chunk[0] == '<':
                        self.text.setTextColor(QColor(200, 0, 0))
                    elif chunk[0] == '>':
                        self.text.setTextColor(QColor(0, 200, 0))
                    else:
                        self.text.setTextColor(QColor(0, 0, 200))

                    self.append(chunk)

    def info(self, errtext):
        self.text.setTextColor(QColor(20, 20, 20))
        self.append(errtext)

    def err(self, errtext):
        self.text.setTextColor(QColor(100, 0, 0))
        self.append(errtext)

    def socketDisconnect(self):
        self.connected = False
        self.err("Disconnected")

    def socketConnect(self):
        self.connected = True
        self.info("Connected")

    def socketError(self, socketError):
        if socketError == QAbstractSocket.RemoteHostClosedError:
            pass
        elif socketError == QAbstractSocket.HostNotFoundError:
            self.err("The host was not found. Please check the host name and "
                     "port settings.")

        elif socketError == QAbstractSocket.ConnectionRefusedError:
            self.err("The connection was refused by the peer. Make sure the "
                     "server is running, and check that the host name "
                     "and port settings are correct.")
        else:
            self.err("The following error occurred: {0}"
                     .format(self.conn.errorString()))

    def save(self):
        fname, sel = QFileDialog.getSaveFileName(
            self,
            'Save Log',)
            #'/path/to/default/directory', FIXME: lastused
            #selectedFilter='*.txt')

        if fname:
            with open(fname, 'w+') as f:
                f.write(self.text.toPlainText())

    def do_connect(self):
        self.conn.abort()
        self.conn.connectToHost(self.host.text(),
                                int(self.port.text()))

    @pyqtSlot()
    def on_connect_clicked(self):
        self.do_connect()
        self.prompt.setFocus()

    @pyqtSlot()
    def on_send_clicked(self):
        if not self.connected:
            self.err("Not connected")
            return
        out = (self.prompt.text() + '\n').encode('ascii')
        self.conn.write(out)

    @pyqtSlot()
    def on_right_on_clicked(self):
        self.action("e1")


def main():
    app = QApplication(sys.argv)
    widget = Main()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
