from functools import partial

import OpenGL.GL as gl
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem

class displaylist(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, obj):
        if hasattr(obj, '_display_list'):
            l = getattr(obj, '_display_list')
            if l:
                gl.glCallList(l)
                return

        l = gl.glGenLists(1)
        gl.glNewList(l, gl.GL_COMPILE)
        self.func(obj)
        gl.glEndList()
        setattr(obj, '_display_list', l)

    def __get__(self, obj, objtype):
        """Support instance methods."""
        return partial(self.__call__, obj)


class HCItem(GLGraphicsItem, object):
    def delChildren(self):
        self._GLGraphicsItem__children = set()

    def redraw(self):
        self._display_list = None


from grid import Grid
