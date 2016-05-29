#!/usr/bin/python2

import sys
import time

#INIT
import os
os.environ['QT_API'] = 'pyqt5'
#/INIT

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSlot, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QTreeWidgetItem, QHeaderView
from PyQt5.uic import loadUi
from PyQt5.QtNetwork import QTcpSocket, QAbstractSocket

from hc import config, parse
from hc.util import enc_msg, dec_msg, xyzfmt

from joystick import Joystick

import Queue

proc_events = QApplication.processEvents


class QHcClient(QTcpSocket):
    n = 0

    def __init__(self, *args):
        super(QHcClient, self).__init__(*args)
        self.waitForReadyRead(100)
        self.setSocketOption(QAbstractSocket.LowDelayOption, 1)
        self.setSocketOption(QAbstractSocket.KeepAliveOption, 1)

        self.queue = Queue.PriorityQueue()

    def cmd(self, cmd):
        ec = cmd.encode('ascii')
        msg = enc_msg(ec, self.n)
        self.n += 1
        self.write(msg)
        self.flush()


red = QColor(200, 0, 0)
green = QColor(0, 200, 0)
blue = QColor(0, 0, 200)

probecmd = 'G38.2 Z{} F{}'


class Main(QMainWindow):
    current_x = 0.
    current_y = 0.
    current_z = 0.
    changes = dict()

    def __init__(self, *args):
        super(Main, self).__init__(*args)

        loadUi('mainwindow.ui', self)

        self.flavor = config.get('flavor', default='smoothie')
        self['connection.host'] = config.get('server_host', 'localhost')
        self['connection.port'] = str(config.get('server_port', '11011'))
        #self.prompt.setText("M114")
        self.prompt.addItem("M114")
        self.prompt.addItem("MULTILINE")

        self.conn = QHcClient(self)
        self.conn.readyRead.connect(self.readSocket)
        self.conn.error.connect(self.socketError)
        self.conn.connected.connect(self.socketConnect)
        self.conn.disconnected.connect(self.socketDisconnect)

        self.connected = False

        self.actionSave_log.triggered.connect(self.save_log_dialog)

        self.actionSave_probe_data.triggered.connect(self.save_probe_data_dialog)
        self.actionLoad_probe_data.triggered.connect(self.load_probe_data_dialog)

        self.actionLoad_G_code.triggered.connect(self.load_gcode_dialog)
        self.actionSave_G_code.triggered.connect(self.save_gcode_dialog)

        self.actionSave_probe_G_code.triggered.connect(self.save_probe_gcode_dialog)

        self.prompt.setFocus()
        self.prompt.lineEdit().returnPressed.connect(self.on_send_clicked)

        # paramtree handlers
        self.ptree.params.sigTreeStateChanged.connect(self.pchange)
        self.ptree.params.param('Connection', 'Connect').sigActivated.connect(self.do_connect)
        self.ptree.params.param('Probe', 'Run probe').sigActivated.connect(self.run_probe)
        self.ptree.params.param('Probe', 'Process').sigActivated.connect(self.process)
        self.ptree.params.param('Probe', 'Save processed G-code').sigActivated.connect(self.save_gcode_dialog)
        self.ptree.params.param('GCode', 'Load G-code').sigActivated.connect(self.load_gcode_dialog)

        # alias
        self.p = self.ptree.get_param
        self.ptree

        self.do_connect()
        self.update_probe()
        self.update_grid()

        #self.commodel = QStandardItemModel(self.comlist)
        #self.comlist.setModel(self.commodel)
        self.comtree.setColumnCount(3)
        self.comtree.setColumnWidth(0, 200)
        self.comtree.setColumnWidth(1, 100)
        self.comtree.setHeaderLabels(['Time', 'Command', 'Response'])
        #self.comtree.header().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comtree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.comtree.header().setStretchLastSection(False)

        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.do_connect)

        joystick = False

        if joystick:
            self.joy = Joystick()
            self.joy.button_down.connect(self.button_down)
            self.joy.axis_moving.connect(self.axis_moving)

        self.init_timer = QTimer()
        self.init_timer.timeout.connect(self.late_init)
        self.init_timer.setSingleShot(True)
        self.init_timer.start(333)

    def late_init(self):
        self.ptree.changing(self.changing)
        self.tool_ipython()

    def tool_ipython(self):
        self.ipy.start()
        self.ipy.push({"self": self})
        #self.ipy.execute('%pylab inline')

    def __getitem__(self, attr):
        """
        Access HCParameTree values via self['some.path']

        Returns cached value from self.changes if parameter is changing
        """

        param = self.ptree.get_param(attr)
        path = self.ptree.params.childPath(param)
        if path is not None:
            pl = '.'.join(path).lower()
            if pl in self.changes:
                return self.changes[pl]

        return param.value()

    def __setitem__(self, attr, val):
        """
        Set HCParameTree values via self['some.path']
        """
        param = self.ptree.get_param(attr)
        param.setValue(val)

    def changing(self, param, value):
        '''
        Keep track of changing parameters
        and store these in self.changes dict
        '''
        path = self.ptree.params.childPath(param)
        if path is not None:
            pl = '.'.join(path).lower()
            # cache changes, eval `value` to param.type
            try:
                # will fail for complex types like colormap so just ignore
                self.changes[pl] = eval('{}({})'.format(param.type(), value))
            except:
                pass
            self.handle_updates(pl)

    def pchange(self, param, changes):
        """
        HCParamTreechange handler
        """

        for param, change, data in changes:
            path = self.ptree.params.childPath(param)
            if path is not None:
                pl = '.'.join(path).lower()
                if pl in self.changes:
                    del self.changes[pl]

                self.handle_updates(pl)

    def handle_updates(self, path=None):
        if path:
            if path.startswith('probe'):
                self.update_probe()

            if path.startswith('grid'):
                self.update_grid()

            if path.startswith('cross'):
                self.update_cross()

            if path.startswith('gcode'):
                self.update_gcode()

            if path.startswith('probe result'):
                self.update_result()

            self.gl.repaint()
            proc_events()

    def load_gcode_dialog(self):
        d = QFileDialog(self)
        d.setNameFilter("GCode (*.ngc *.gcode);;All files (*.*)")
        d.exec_()
        name = d.selectedFiles()[0]
        try:
            self.gl.gcode.load_gcode(name)

            # prefill probe width / height
            xmin, xmax = self.gl.gcode.limits['X']
            ymin, ymax = self.gl.gcode.limits['Y']
            zmin, zmax = self.gl.gcode.limits['Z']
            self['probe.width'] = xmax
            self['probe.height'] = ymax
            self['gcode.width'] = xmax
            self['gcode.height'] = ymax
            self['gcode.min z'] = zmin
            self['gcode.max z'] = zmax

            self.gcode_path = name
            print('Loaded {}'.format(name))
        except IOError as e:
            print('Unable to load {}'.format(name))
            print(e)

    def save_gcode_dialog(self):
        d = QFileDialog(self)
        d.setNameFilter("GCode (*.ngc *.gcode);;All files (*.*)")
        d.exec_()
        name = d.selectedFiles()[0]
        try:
            if self.gl.postgcode.orig:
                self.gl.postgcode.save_gcode(name)
                print('Saved post-processed g-code to {}'.format(name))
            elif self.gl.gcode.orig:
                self.gl.gcode.save_gcode(name)
                print('Saved original g-code to {}'.format(name))
            else:
                print('Nothing to save')

        except IOError as e:
            print('Unable to save to {}'.format(name))
            print(e)

    def append(self, text):
        self.text.append(text)

    def handle_response(self, idx, txt):
        root = self.comtree.invisibleRootItem()
        item = root.child(idx)

        item.setText(0, time.strftime("%Y.%m.%d. %H:%M:%S", time.localtime()))
        if not txt:
            txt = 'ok'
        item.setText(2, txt)
        item.setCheckState(0, Qt.Checked)
        self.comtree.scrollToItem(item)

        cmd = item.text(1)

        proc_events()

        if 'G0' in cmd:
            x, y, z = parse.xyz(cmd[2:])
            # should probably emit signals

            self.current_x = x
            self.current_y = y
            self.current_z = z

        if 'G38.2' in cmd:
            try:
                # e.g. Probe not tripped from LinuxCNC
                # (we get error message from backend)
                if 'error' in txt:
                    z = -999.0
                else:
                    z = parse.probe(txt)
            except:
                self.err('Unable to parse probe: {}'.format(txt))
                self.err('Is your flavor ({}) correct?'.format(self.flavor))
                z = -999.0

            self.gl.result.data.append((self.current_x, self.current_y, z))
            self.update_result()
            self['probe result.lowest'] = min(self['probe result.lowest'], z)
            self['probe result.highest'] = max(self['probe result.highest'], z)
            self['probe result.last'] = z

    def save_probe_data_dialog(self):
        if not self.gl.result.data:
            # err not much to save
            return

        fname, sel = QFileDialog.getSaveFileName(
            self,
            'Save Log',)
            #'/path/to/default/directory', FIXME: lastused
            #selectedFilter='*.txt')

        if fname:
            self.save_probe_data(fname)

    def save_probe_data(self, fname):
        with open(fname, 'w') as f:
            for x, y, z in self.gl.result.data:
                f.write("{:04.2f} {:04.2f} {:04.2f}\n".format(x, y, z))

    def load_probe_data_dialog(self):
        d = QFileDialog(self)
        d.setNameFilter("Log data (*.txt *.log);;All files (*.*)")
        d.exec_()
        fname = d.selectedFiles()[0]
        if fname:
            self.load_probe_data(fname)

    def load_probe_data(self, fname):
        with open(fname, 'r') as f:
            d = (map(lambda x: map(float, x.split()), f.readlines()))

        self.gl.result.data = d
        self.update_result()

    @pyqtSlot()
    def on_save_clicked(self):
        root = self.comtree.invisibleRootItem()
        {'name': 'Visible', 'type': 'bool', 'value': 1},
        count = root.childCount()

        parts = []
        for i in range(count):
            item = root.child(i)
            time = item.text(0)
            cmd = item.text(1)
            resp = item.text(2)
            parts.append((time, cmd, resp))

        fname, sel = QFileDialog.getSaveFileName(
            self,
            'Save Log',)
            #'/path/to/default/directory', FIXME: lastused
            #selectedFilter='*.txt')

        if fname:
            with open(fname, 'w') as f:
                for time, cmd, resp in parts:
                    f.write('{}\t{}\t{}\n'.format(time, cmd, resp))

    def readSocket(self):
        def handle(r):
            if not r:
                return

            #print('buffered', r)
            (idx, txt) = dec_msg(r)
            if idx is not None:
                self.handle_response(idx, txt)

        buffer = ''

        while True:
            r = str(self.conn.readLine())

            if not r:
                handle(buffer)
                if self.conn.canReadLine():
                    buffer = ''
                    continue

                break

            if r[0] == '/':
                _, msg = dec_msg(r)
                self.append('{}'.format(msg))
                continue

            if r[0] == '[':
                handle(buffer)
                buffer = r
                continue

            buffer += r

    def info(self, errtext):
        self.text.setTextColor(QColor(20, 20, 20))
        self.append(errtext)

    def err(self, errtext):
        self.text.setTextColor(QColor(100, 0, 0))
        self.append(errtext)

    def socketDisconnect(self):
        self.err("Disconnected")
        self.connected = False
        self.info("Reconnecting")
        self.reconnect_timer.start(1000)

    def socketConnect(self):
        self.connected = True
        self.reconnect_timer.stop()
        self.info("Connected to {}:{}".format(self['connection.host'],
                                              self['connection.port']))
        self.ptree.collapse_group('connection')

    def socketError(self, socketError):
        # backoff
        self.reconnect_timer.setInterval(self.reconnect_timer.interval() * 2)

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

    def save_log_dialog(self):
        fname, sel = QFileDialog.getSaveFileName(
            self,
            'Save Log',)
            #'/path/to/default/directory', FIXME: lastused
            #selectedFilter='*.txt')

        if fname:
            with open(fname, 'w') as f:
                f.write(self.text.toPlainText())

    def save_probe_gcode_dialog(self):
        fname, sel = QFileDialog.getSaveFileName(
            self,
            'Save probe G-code',)
            #'/path/to/default/directory', FIXME: lastused
            #selectedFilter='*.txt')

        if fname:
            with open(fname, 'w') as f:
                for code in self.gen_probe_gcode(self.get_probe_points()):
                    f.write(code + '\n')

    def do_connect(self):
        self.conn.abort()
        self.info("Connecting to {}:{}".format(self['connection.host'],
                                               self['connection.port']))
        self.conn.connectToHost(self['connection.host'],
                                int(self['connection.port']))

    @pyqtSlot()
    def on_prompt_activated(self):
        pass

    def run_cmd(self, cmd):
        item = QTreeWidgetItem(self.comtree)

        item.setText(0, time.strftime("%Y.%m.%d. %H:%M:%S", time.localtime()))
        item.setText(1, cmd)

        for i in range(3):
            item.setTextAlignment(i, Qt.AlignTop)

        item.setForeground(1, QtGui.QBrush(green))
        item.setForeground(2, QtGui.QBrush(red))

        self.comtree.scrollToItem(item)
        self.conn.cmd(cmd)
        proc_events()

    @pyqtSlot()
    def on_send_clicked(self):
        if not self.connected:
            self.err("Not connected")
            return
        out = self.prompt.currentText()
        self.run_cmd(out)

    # FIXME: should go to hc lib
    def gen_probe_grid(self, rows, cols, w, h, x_margin, y_margin, start_z):
        w = w - x_margin * 2.
        h = h - y_margin * 2.

        if rows <= 0 or cols <= 0:
            return []

        if cols == 1 or rows == 1:
            return []

        xstep = w / (cols - 1)
        ystep = h / (rows - 1)

        cx = x_margin
        cy = y_margin

        out = []

        for i in range(rows):
            for j in range(cols):
                out.append((cx, cy, start_z))
                cx += xstep

            cx = x_margin
            cy += ystep

        return out

    def get_probe_points(self):
        m = self['probe.margin']
        probe_points = self.gen_probe_grid(
            self['probe.rows'], self['probe.cols'],
            self['probe.width'], self['probe.height'],
            m, m,
            self['probe.start z'])

        return probe_points

    def gen_probe_gcode(self, points):
        feed = self['probe.feedrate']
        depth = self['probe.max depth']
        sz = self['probe.start z']

        yield 'G90'
        for point in points:
            yield 'G0 {}'.format(xyzfmt(*point))
            yield probecmd.format(depth, feed)
            # go straight up startz/2.
            yield 'G0 Z{}'.format(sz / 2.)

    def run_probe(self):
        # clean probe result
        self.gl.result.data = []

        for code in self.gen_probe_gcode(self.get_probe_points()):
            self.run_cmd(code)

    def update_gcode(self):
        self.gl.gcode.setVisible(self['gcode.visible'])

    def update_probe(self):
        probe_points = self.get_probe_points()
        self.gl.probelist.probe_points = probe_points
        self.gl.probelist.update()

    def update_result(self):
        self.gl.result.setVisible(self['probe result.visible'])
        self.gl.result.offset = self['probe result.offset']
        self.gl.result.multiply = self['probe result.multiply']
        self.gl.result.snapz = self['probe result.snap z']
        self.gl.result.colormap = self['probe result.gradient']
        self.gl.result.opts['drawEdges'] = self['probe result.draw edges']

        self.gl.result.update_data()

    def update_grid(self):
        w = self['grid.width']
        h = self['grid.height']
        self.gl.grid.setSize(w, h, 1)
        self.gl.grid.resetTransform()
        self.gl.grid.translate(w / 2., h / 2., -0.05)
        self.gl.grid.setVisible(self['grid.visible'])
        self.gl.grid.redraw()

    def update_cross(self):
        s = self['cross.size']
        pos = []
        for i in ['x', 'y', 'z']:
            pos.append(self['cross.pos.{}'.format(i)])

        self.gl.cross.size = s
        self.gl.cross.resetTransform()
        self.gl.cross.translate(*pos)
        self.gl.cross.setVisible(self['cross.visible'])

    def process(self):
        self.info('Processing')
        self.precision = 0.1

        res = self.gl.result.data[:]
        if not res:
            self.err('No probe results')
            return

        datapath = '/tmp/hc_probedata'

        print(res)
        with open(datapath, 'w') as f:
            for x, y, z in res:
                f.write("{:04.2f} {:04.2f} {:04.2f}\n".format(x, y, z))

        script = config.get('leveling_tool', 'scale_gcode.py')

        gcpath = os.path.abspath(self.gcode_path)
        args = '{} 1-999999 --zlevel {} {:.2f}'.format(gcpath,
                                                       datapath,
                                                       self.precision)

        args = args.split()
        self.info('Calling "{}"'.format(" ".join([script] + args)))
        proc_events()

        import subprocess
        proc = subprocess.Popen([script] + args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, close_fds=True)

        (stdout, stderr) = proc.communicate()

        print("stderr:")
        print(stderr)
        print("stdout:")
        print(stdout)

        self.info('Done. Saving to /tmp/hc_postgcode')

        fpath = '/tmp/hc_postgcode'
        with open(fpath, 'w') as f:
            f.write(stdout)

        self.gl.postgcode.load_gcode(fpath)
        self.info('Loaded post-processed G-code')

    # joystick handlers
    def axis_moving(self, axis, value):
        #self.run_cmd('G91')
        m = ['x', 'y', 'z', 'a']
        if abs(value) < 0.1:
            return

        value = value / 10
        #self.run_cmd('G0 {}{}'.format(m[axis], value))
        self.run_cmd('/jog {} {:04.2f}'.format(m[axis], value))

    def button_down(self, button):
        pass


def main():
    app = QApplication(sys.argv)
    widget = Main()
    widget.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
