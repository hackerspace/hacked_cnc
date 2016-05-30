import OpenGL.GL as gl

from hc.ui.glitems import displaylist, HCItem


class Cross(HCItem):
    size = 10

    @displaylist
    def paint(self):
        self.setupGLState()

        size = self.size

        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(1, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(size, 0, 0)

        gl.glColor3f(0, 1, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, size, 0)

        gl.glColor3f(0, 0, 1)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(0, 0, size)
        gl.glEnd()
