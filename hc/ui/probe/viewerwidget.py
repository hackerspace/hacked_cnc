#!/usr/bin/python
# GPLv2
import sys
import os
from OpenGL.GL import *
from PyQt5 import QtGui, uic, QtCore, QtWidgets
from PyQt5.QtOpenGL import *

import util
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import numpy as np

from items import *


class HCViewerWidget(gl.GLViewWidget):
    ele = 0
    azi = 0
    gcodelist = -1
    _probelist = None
    _proberes = None

    probe_results = []

    def __init__(self, parent=None):
        super(HCViewerWidget, self).__init__(parent)

        self.gcode_points = []
        self.probe_points = [(10, 10, 10)]
        self.oldpos = 0, 0
        self.filename = ''
        self.objsize = 0, 0, 0
        self.gcodesize = 0
        self._oc = (0, 0, 0)
        self._ogc = None

        self.setCameraPosition(distance=40, azimuth=-90)

        self.grid = gl.GLGridItem()
        self.grid.translate(10, 10, -0.01)
        self.cross = Cross()

        self.probelist = ProbeList()
        shader = 'normalColor'
        shader = 'heightColor'
        self.proberes = ProbeResult(
            x=np.arange(1), y=np.arange(1),
            z=np.zeros((1, 1)),
            edgeColor=(0.9, 0.3, 0.3, 1),
            drawEdges=True,
            #shader='shaded', color=(0.5, 0.5, 1, 1))
            shader=shader)
            #computeNormals=False, smooth=False,
            #glOptions='additive')

        #self.proberes.shader()['colorMap'] = np.array([0.2, 2, 0.5, 0.2, 1, 1, 0.2, 0, 2])

        self.addItem(self.grid)
        self.addItem(self.cross)
        self.addItem(self.probelist)
        self.addItem(self.proberes)

        self.gcode = GCode()
        self.postgcode = GCode()

        #self.addItem(self.gcode)
        self.addItem(self.postgcode)

    def autoorbit(self):
        self.ele += 0
        self.azi += 0.1
        self.orbit(self.azi, self.ele)

    def initializeGL(self):
        glShadeModel(GL_SMOOTH)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
