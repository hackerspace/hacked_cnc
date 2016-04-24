import numpy as np
import pyqtgraph.opengl as gl
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from OpenGL.GL import *


import util


class Cross(GLGraphicsItem):
    cross_size = 10

    def __init__(self):
        GLGraphicsItem.__init__(self)

    def paint(self):
        self.setupGLState()

        size = self.cross_size

        glBegin(GL_LINES)
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(1 * size, 0, 0)

        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1 * size, 0)

        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1 * size)
        glEnd()


class ProbeList(GLGraphicsItem):
    list = None
    size = 10
    probe_points = [(1, 1, 1)]

    def paint(self):
        self.setupGLState()
        if self.list:
            glCallList(self.list)
            return

        s = self.size / 2.
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        for i, p in enumerate(self.probe_points):
            _x, _y, _z = map(float, [p[0], p[1], p[2]])
            glBegin(GL_LINE_STRIP)
            glColor3f(i / float(len(self.probe_points)), 0.7, 0.7)
            _z = 0
            glVertex3f(_x, _y, _z - s)
            glVertex3f(_x, _y, _z + s)
            glEnd()

        glEndList()
        glCallList(self.list)

    def update(self):
        self.list = None
        super(ProbeList, self).update()


class ProbeResult(gl.GLSurfacePlotItem):
    # fixme: use data instead of this
    probe_results = []
    offset = 0
    exaggerate = 1

    def update_results(self):
        probe_results = self.probe_results

        if not probe_results:
            return

        lx = len(set(map(lambda x: x[0], probe_results)))
        ly = len(set(map(lambda x: x[1], probe_results)))

        x = []
        y = []
        z = np.zeros((lx, ly))

        row = -1

        for i, r in enumerate(probe_results):
            if r[0] not in x:
                x.append(r[0])

            if r[1] not in y:
                y.append(r[1])
                row += 1

            z[i % lx, row] = (r[2] + self.offset) * self.exaggerate

        self.setData(x=np.array(x), y=np.array(y), z=z)


class GCode(GLGraphicsItem):
    list = None
    gcode_points = []
    probe_points = [(10, 10, 10)]
    oldpos = 0, 0
    filename = ''
    objsize = 0, 0, 0
    gcodesize = 0
    _oc = (0, 0, 0)
    _ogc = None
    orig = None

    def object_size(self, obj):
        try:
            x = map(lambda _x: float(_x['X']), obj)
            xmax = max(x)
            xmn = min(x)

            y = map(lambda _y: float(_y['Y']), obj)
            ymax = max(y)
            ymn = min(y)

            z = map(lambda _z: float(_z['Z']), obj)
            zmax = max(z)
            zmn = min(z)

            return (xmax - xmn), (ymax - ymn), (zmax - zmn)
        except ValueError:
            return 0, 0, 0

    def _recalc_object_center(self, obj):
        if len(obj) > 2:
            obj = obj[1:-1]
        x = sum(map(lambda _x: float(_x['X']), obj))
        y = sum(map(lambda _x: float(_x['Y']), obj))
        z = sum(map(lambda _x: float(_x['Z']), obj))
        l = len(obj)
        if l == 0:
            self._oc = 0, 0, 0
        self._oc = (x / l, y / l, z / l)

    def paint(self):
        self.setupGLState()
        if self.list:
            glCallList(self.list)
            return

        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE) #_AND_EXECUTE)
        glBegin(GL_LINE_STRIP)
        for i, p in enumerate(self.gcode_points):
            _x, _y, _z = map(float, [p['X'], p['Y'], p['Z']])
            glColor3f(i / float(len(self.gcode_points)), 0.5, float(p['L']))
            glVertex3f(_x, _y, _z)
        glEnd()
        glEndList()

        glCallList(self.list)

    def load_gcode(self, filename):
        if self.list:
            glDeleteLists(self.list, 1)
            self.list = None

        self.filename = filename
        with open(filename) as fd:
            self.orig = fd.read()

        self.gcode_points = util.load_gcode_commands(self.orig)
        s = self.object_size(self.gcode_points)

        self.gcodesize = len(self.gcode_points)
        self.objsize = s
        self._recalc_object_center(self.gcode_points)

    def save_gcode(self, filename):
        with open(filename, 'w') as fd:
            fd.write(self.orig)
