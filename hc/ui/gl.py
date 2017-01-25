
import pyqtgraph.opengl as pygl

class GLViewWidget(pygl.GLViewWidget):
    def getViewport(self, *args, **kwargs):
        x0, y0, w, h = super(GLViewWidget, self).getViewport(*args, **kwargs)
        return x0, y0, w, max(1, h)
