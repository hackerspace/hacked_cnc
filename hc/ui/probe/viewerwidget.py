#!/usr/bin/python2
# GPLv2
from OpenGL.GL import *
from PyQt5.QtOpenGL import *
from PyQt5 import QtGui

import numpy as np

from hc.ui.gl import GLViewWidget
from hc.ui.glitems import *


def _gl_vector(array, *args):
    '''
    Convert an array and an optional set of args into a flat vector of GLfloat
    '''
    array = np.array(array)
    if len(args) > 0:
        array = np.append(array, args)
    vector = (GLfloat * len(array))(*array)
    return vector


class HCViewerWidget(GLViewWidget):
    ele = 0
    azi = 0
    gcodelist = -1

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

        self.opts['center'] = QtGui.QVector3D(10, 0, 0)
        self.opts['fov'] = 90
        self.setCameraPosition(distance=15, elevation=20, azimuth=-90)

        self.grid = Grid()
        self.cross = Cross()

        self.probelist = ProbeList()

        self.result = ProbeResult(
            x=np.arange(1), y=np.arange(1),
            z=np.zeros((1, 1)),
            edgeColor=(0.9, 0.3, 0.3, 1),
            shader='shaded',
            glOptions='translucent')

        self.addItem(self.grid)
        self.addItem(self.cross)
        self.addItem(self.probelist)
        self.addItem(self.result)

        self.gcode = GCode()
        self.postgcode = GCode()

        self.addItem(self.gcode)
        self.addItem(self.postgcode)

        self.model = Model()
        self.addItem(self.model)

        self.ruler = Ruler()
        self.ruler.translate(0, -3, 0)
        self.addItem(self.ruler)

        self.yruler = YRuler()
        self.yruler.translate(-3, 0, 0)
        self.addItem(self.yruler)

        self.zruler = ZRuler()
        self.zruler.translate(-3, -3, 0)
        self.addItem(self.zruler)

    def autoorbit(self):
        self.ele += 0
        self.azi += 0.1
        self.orbit(self.azi, self.ele)

    def initializeGL(self):
        glShadeModel(GL_SMOOTH)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_CULL_FACE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)

        glLightfv(GL_LIGHT0, GL_POSITION, _gl_vector(.5, .5, 1, 0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, _gl_vector(.5, .5, 1, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, _gl_vector(1, 1, 1, 1))
        glLightfv(GL_LIGHT1, GL_POSITION, _gl_vector(1, 0, .5, 0))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, _gl_vector(.5, .5, .5, 1))
        glLightfv(GL_LIGHT1, GL_SPECULAR, _gl_vector(1, 1, 1, 1))

        glShadeModel(GL_SMOOTH)

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)

        glMaterialfv(GL_FRONT, GL_AMBIENT, _gl_vector(0.192250, 0.192250, 0.192250))
        glMaterialfv(GL_FRONT, GL_DIFFUSE, _gl_vector(0.507540, 0.507540, 0.507540))
        glMaterialfv(GL_FRONT, GL_SPECULAR, _gl_vector(.5082730, .5082730, .5082730))

        glMaterialf(GL_FRONT, GL_SHININESS, .4 * 128.0)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_FRONT)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def paintGL(self, *args, **kwargs):
        super(HCViewerWidget, self).paintGL(*args, **kwargs)
        # FIXME: we can render texts over gl
        #self.renderText(20, 20, 'X:   0.000')
        #self.renderText(20, 40, 'Y:   0.000')
        #self.renderText(20, 60, 'Z:  -1.000')
