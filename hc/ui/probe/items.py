import numpy as np
from itertools import izip

import pyqtgraph.opengl as gl
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from OpenGL.GL import *

from hc import parse, log


class Cross(GLGraphicsItem):
    size = 10

    def __init__(self):
        GLGraphicsItem.__init__(self)

    def paint(self):
        self.setupGLState()

        size = self.size

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
    probe_results = []
    offset = 0
    multiply = 1
    snapz = 1
    colormap = None
    data = None
    snapped_data = None

    def process(self):
        if not self.data:
            return

        res = self.data[:]
        sres = sorted(res, key=lambda x: x[2])
        self.minz = sres[0][2]
        self.maxz = sres[-1][2]
        self.range = self.maxz - self.minz

        nres = []

        for x, y, z in res:
            #nz = z - self.maxz
            nz = z - self.minz
            nz = nz
            nres.append((x, y, nz))

        self.snapped_data = nres

    def update_data(self):
        self.process()

        if self.snapz:
            data = self.snapped_data
        else:
            data = self.data

        if not data:
            return

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

    def paint(self):
        self.setupGLState()

        glDisable(GL_LIGHTING)

        if self.list:
            glCallList(self.list)
            return

        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE) #_AND_EXECUTE)
        glBegin(GL_LINE_STRIP)
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

            glColor3f(i / float(self.gcodesize), 0.5, _l)

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

        self.gcode_points, self.limits = parse.gcode(self.orig)
        self.gcodesize = len(self.gcode_points)

    def save_gcode(self, filename):
        with open(filename, 'w') as fd:
            fd.write(self.orig)


class Model(GLGraphicsItem):
    list = None
    mesh = None
    edges = False
    wireframe = False

    def __init__(self):
        GLGraphicsItem.__init__(self)

    def load(self, path):
        try:
            import trimesh
        except:
            log.msg('trimesh not available')

        # load a file by name or from a buffer
        l = trimesh.load_mesh(path)
        if isinstance(l, trimesh.Trimesh):
            self.mesh = l
        else:
            log.msg('Unable to load mesh, multiple files loaded?')

    def paint(self):
        if not self.mesh:
            return

        self.setupGLState()
        if self.list:
            glCallList(self.list)
            return

        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        glEnable(GL_LIGHTING)
        if self.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glEnable(GL_COLOR_MATERIAL)
        glColor4ub(200, 200, 255, 100)
        self.draw_mesh_faces_flat(self.mesh, self.edges)
        glDisable(GL_LIGHTING)

        if self.edges:
            self.draw_edges(self.mesh)

        glEndList()
        glCallList(self.list)

    def draw_edges(self, mesh):
        l = len(mesh.edges)

        glBegin(GL_LINES)
        for n, edge in enumerate(mesh.edges):
            glColor3f(n / float(l), 0.5, 0.5)
            edge = tuple(edge)
            glVertex3f(*mesh.vertices[edge[0]])
            glVertex3f(*mesh.verticess[edge[1]])
        glEnd()

    def draw_mesh_faces_flat(self, mesh, will_draw_edges=True):
        '''
        Takes a TriMesh parameter mesh and draws it, setting as little OpenGL state as possible.
        Lighting and materials and colors be specified before this function is entered.
        If the parameters indicates that edges will be drawn, then glPolygonOffset will be used.
        '''

        if will_draw_edges:
            ## This offset guarantees that all polygon faces have a z-buffer value at least 1 greater.
            glPolygonOffset(1.0, 1.0)
            glEnable(GL_POLYGON_OFFSET_FILL)

        glBegin(GL_TRIANGLES)
        for face, normal in izip(mesh.faces, mesh.face_normals):
            glNormal3f(*normal)
            for vertex_index in face:
                glVertex3f(*mesh.vertices[vertex_index])
        glEnd()

        glDisable(GL_POLYGON_OFFSET_FILL)
