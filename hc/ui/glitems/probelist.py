import OpenGL.GL as gl

from hc.ui.glitems import displaylist, HCItem


class ProbeList(HCItem):
    size = 10
    probe_points = [(1, 1, 1)]

    @displaylist
    def paint(self):
        self.setupGLState()

        gl.glBegin(gl.GL_LINES)

        s = self.size / 2.
        for i, p in enumerate(self.probe_points):
            _x, _y, _z = map(float, [p[0], p[1], p[2]])
            gl.glColor3f(i / float(len(self.probe_points)), 0.7, 0.7)
            _z = 0
            gl.glVertex3f(_x, _y, _z - s)
            gl.glVertex3f(_x, _y, _z + s)

        gl.glEnd()
