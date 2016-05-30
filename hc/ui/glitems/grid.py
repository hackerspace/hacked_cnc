import numpy as np

import OpenGL.GL as gl
from PyQt5 import QtGui

from hc.ui.glitems import displaylist, HCItem


# based on pyqtgraphs's grid
class Grid(HCItem):
    """
    Displays a wire-grame grid.
    """

    def __init__(self, size=None, color=None, antialias=True, glOptions='translucent'):
        super(Grid, self).__init__()
        self.setGLOptions(glOptions)
        self.antialias = antialias
        if size is None:
            size = QtGui.QVector3D(20, 20, 1)
        self.setSize(size=size)
        self.setSpacing(1, 1, 1)

    def setSize(self, x=None, y=None, z=None, size=None):
        """
        Set the size of the axes (in its local coordinate system; this does not affect the transform)
        Arguments can be x,y,z or size=QVector3D().
        """
        if size is not None:
            x = size.x()
            y = size.y()
            z = size.z()
        self.__size = [x, y, z]
        self.update()

    def size(self):
        return self.__size[:]

    def setSpacing(self, x=None, y=None, z=None, spacing=None):
        """
        Set the spacing between grid lines.
        Arguments can be x,y,z or spacing=QVector3D().
        """
        if spacing is not None:
            x = spacing.x()
            y = spacing.y()
            z = spacing.z()
        self.__spacing = [x, y, z]
        self.update()

    def spacing(self):
        return self.__spacing[:]

    @displaylist
    def paint(self):
        self.setupGLState()

        if self.antialias:
            gl.glEnable(gl.GL_LINE_SMOOTH)
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
            gl.glHint(gl.GL_LINE_SMOOTH_HINT, gl.GL_NICEST)
        gl.glBegin(gl.GL_LINES)

        x, y, z = self.size()
        xs, ys, zs = self.spacing()
        xvals = np.arange(-x / 2., x / 2. + xs * 0.001, xs)
        yvals = np.arange(-y / 2., y / 2. + ys * 0.001, ys)
        gl.glColor4f(1, 0.5, 0.5, .3)
        for x in xvals:
            gl.glVertex3f(x, yvals[0], 0)
            gl.glVertex3f(x,  yvals[-1], 0)
        for y in yvals:
            gl.glVertex3f(xvals[0], y, 0)
            gl.glVertex3f(xvals[-1], y, 0)

        gl.glEnd()
