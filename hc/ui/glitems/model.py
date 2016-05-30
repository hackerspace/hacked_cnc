from itertools import izip

import OpenGL.GL as gl

from hc import log
from hc.ui.glitems import displaylist, HCItem


class Model(HCItem):
    mesh = None
    edges = not True
    wireframe = False

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

    @displaylist
    def paint(self):
        if not self.mesh:
            return

        self.setupGLState()

        gl.glEnable(gl.GL_LIGHTING)
        if self.wireframe:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        else:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glColor4ub(200, 200, 255, 220)
        self.draw_mesh_faces_flat(self.mesh, self.edges)
        gl.glDisable(gl.GL_LIGHTING)

        if self.edges:
            self.draw_edges(self.mesh)

    def draw_edges(self, mesh):
        l = len(mesh.edges)

        gl.glBegin(gl.GL_LINES)
        for n, edge in enumerate(mesh.edges):
            gl.glColor3f(n / float(l), 0.5, 0.5)
            edge = tuple(edge)
            gl.glVertex3f(*mesh.vertices[edge[0]])
            gl.glVertex3f(*mesh.vertices[edge[1]])
        gl.glEnd()

    def draw_mesh_faces_flat(self, mesh, will_draw_edges=True):
        '''
        Takes a TriMesh parameter mesh and draws it, setting as little OpenGL state as possible.
        Lighting and materials and colors be specified before this function is entered.
        If the parameters indicates that edges will be drawn, then glPolygonOffset will be used.
        '''

        if will_draw_edges:
            ## This offset guarantees that all polygon faces have a z-buffer value at least 1 greater.
            gl.glPolygonOffset(1.0, 1.0)
            gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)

        gl.glBegin(gl.GL_TRIANGLES)
        for face, normal in izip(mesh.faces, mesh.face_normals):
            gl.glNormal3f(*normal)
            for vertex_index in face:
                gl.glVertex3f(*mesh.vertices[vertex_index])
        gl.glEnd()

        gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)
