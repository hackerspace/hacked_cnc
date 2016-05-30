import OpenGL.GL as gl

from hc import parse
from hc.ui.glitems import displaylist, HCItem


class GCode(HCItem):
    gcode_points = []
    probe_points = [(10, 10, 10)]
    oldpos = 0, 0
    filename = ''
    objsize = 0, 0, 0
    gcodesize = 0
    _oc = (0, 0, 0)
    _ogc = None
    orig = None

    @displaylist
    def paint(self):
        self.setupGLState()

        # FIXME: configurable?
        #glLineWidth(1)
        gl.glBegin(gl.GL_LINE_STRIP)
        _x = 0.0
        _y = 0.0
        _z = 0.0
        _l = 0.0

        for i, p in enumerate(self.gcode_points):
            if 'X' in p:
                _x = p['X']
            if 'Y' in p:
                _y = p['Y']
            if 'Z' in p:
                _z = p['Z']

            if 'L' in p:
                _l = p['L']

            gl.glColor3f(i / float(self.gcodesize), 0.5, _l)

            gl.glVertex3f(_x, _y, _z)
        gl.glEnd()

    def load_gcode(self, filename):
        self.filename = filename
        with open(filename) as fd:
            self.orig = fd.read()

        self.gcode_points, self.limits = parse.gcode(self.orig)
        self.gcodesize = len(self.gcode_points)
        self.redraw()

    def save_gcode(self, filename):
        with open(filename, 'w') as fd:
            fd.write(self.orig)
