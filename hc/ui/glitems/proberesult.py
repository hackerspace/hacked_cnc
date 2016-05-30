import numpy as np
import pyqtgraph.opengl as pygl
from hc.ui.glitems import displaylist, HCItem


class ProbeResult(pygl.GLSurfacePlotItem):
    probe_results = []
    offset = 0
    multiply = 1
    snapz = 1
    colormap = None
    data = None
    snapped_data = None

    def process(self):
        res = self.data[:]
        sres = sorted(res, key=lambda x: x[2])
        self.minz = sres[0][2]
        self.maxz = sres[-1][2]
        self.range = self.maxz - self.minz

        nres = []

        for x, y, z in res:
            nz = z - self.minz
            nz = nz
            nres.append((x, y, nz))

        if self.range == 0:
            self.range = 1
        self.snapped_data = nres

    def update_data(self):
        if not self.data:
            return

        self.process()

        if self.snapz:
            data = self.snapped_data
        else:
            data = self.data

        lx = len(set(map(lambda x: x[0], data)))
        ly = len(set(map(lambda x: x[1], data)))

        x = []
        y = []
        z = np.zeros((lx, ly))
        colors = np.zeros((lx, ly, 4))

        row = -1

        for i, r in enumerate(data):
            if r[0] not in x:
                x.append(r[0])

            if r[1] not in y:
                y.append(r[1])
                row += 1

            z[i % lx, row] = (r[2] + self.offset) * self.multiply

            if self.snapz:
                index = r[2] * 1 / self.range
            else:
                index = (r[2] - self.minz) * 1 / self.range

            if self.colormap:
                c = self.colormap.map(index)
                c = c / 255.
            else:
                c = 0.5

            colors[i % lx, row] = c

        self.setData(x=np.array(x), y=np.array(y), z=z, colors=colors)
        # like self.redraw but this one does not inherit HCItem
        self._display_list = None

    @displaylist
    def paint(self):
        pygl.GLSurfacePlotItem.paint(self)

