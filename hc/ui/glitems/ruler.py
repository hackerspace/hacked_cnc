import OpenGL.GL as gl

from hc.ui.glitems import displaylist, HCItem, Text


class Ruler(HCItem):
    x = 0.
    y = 0.
    size = 10
    subsize = 1
    labels_down = True

    def __init__(self):
        super(Ruler, self).__init__()
        self.reset()
        self.redraw()

    def add_texts(self):
        s = self.size
        sb = self.subsize
        x = self.x
        off = -0.5

        self.text = Text(s - x, center=True)
        h = self.text.height
        if self.labels_down:
            d = 1
            y = -0.1 - self.text.height / 2.
        else:
            d = -1
            y = 0.1 + self.text.height / 2.

        # do not draw middle text if it doesn't fit
        if self.size > h + self.text.width:
            self.text.translate(s / 2., y, 0)
            self.text.setParentItem(self)

        self.textl = Text(x, center=True)
        self.textl.rotate(-90, 0, 0, 1)
        y = off - self.textl.width + sb
        y *= d
        self.textl.translate(0, y, 0)
        self.textl.setParentItem(self)
        self.textr = Text(s + x, center=True)
        self.textr.rotate(-90, 0, 0, 1)
        y = off - self.textr.width + sb
        y *= d
        self.textr.translate(s, y, 0)
        self.textr.setParentItem(self)

    def redraw(self):
        self.delChildren()
        self.add_texts()
        self._display_list = None

    def reset(self):
        self.resetTransform()

    @displaylist
    def paint(self):
        self.setupGLState()

        size = self.size
        subsize = self.subsize / 2.

        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(1, 0, 0)
        gl.glVertex3f(0, 0, 0)
        gl.glVertex3f(size, 0, 0)

        for i in [0, 1]:
            for j in [-1, 1]:
                gl.glVertex3f(i * size, 0, 0)
                gl.glVertex3f(i * size, j * subsize, 0)

        gl.glEnd()


class YRuler(Ruler):
    labels_down = False

    def reset(self):
        super(YRuler, self).reset()
        self.rotate(90, 0, 0, 1)


class ZRuler(Ruler):
    labels_down = False

    def reset(self):
        super(ZRuler, self).reset()
        self.rotate(90, 0, 0, 1)
        self.rotate(90, 1, 0, 0)
