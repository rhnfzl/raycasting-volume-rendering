import math
import numpy as np
try:
    # The Python OpenGL package can be found at
    # http://PyOpenGL.sourceforge.net/
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False


class TrackballInteractor:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.lmx = self.lmy = 0
        self.last_position = [0.0, 0.0, 0.0]
        self.axis = [0.0, 0.0, 0.0]
        self.angle = 0.0
        self.rotating = False
        self.trackball_x_form = np.zeros(16)
        self.trackball_x_form[0] = 1.0
        self.trackball_x_form[5] = 1.0
        self.trackball_x_form[10] = 1.0
        self.trackball_x_form[15] = 1.0

    def set_dimensions(self, width, height):
        self.width = width
        self.height = height

    def get_transformation_matrix(self):
        return self.trackball_x_form

    def set_mouse_position(self, x, y):
        self.lmx = x
        self.lmy = y
        TrackballInteractor.trackball_ptov(self.lmx, self.lmy, self.width, self.height, self.last_position)

    @staticmethod
    def trackball_ptov(x, y, width, height, v):
        radius = min(width, height) - 20
        v[0] = (2.0 * x - width) / radius
        v[1] = (height - 2.0 * y) / radius

        d = math.sqrt(v[0] * v[0] + v[1] * v[1])
        v[2] = math.cos((math.pi / 2.0) * (d if d < 1.0 else 1.0))
        a = 1.0 / math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        v[0] = v[0] * a
        v[1] = v[1] * a
        v[2] = v[2] * a

    def drag(self, mx, my):
        current_position = np.zeros(3)

        TrackballInteractor.trackball_ptov(mx, my, self.width, self.height, current_position)

        diff = current_position - self.last_position

        if diff[diff != 0].size > 0:
            self.angle = 90.0 * np.linalg.norm(diff)
            self.axis[0] = self.last_position[1] * current_position[2] - self.last_position[2] * current_position[1]
            self.axis[1] = self.last_position[2] * current_position[0] - self.last_position[0] * current_position[2]
            self.axis[2] = self.last_position[0] * current_position[1] - self.last_position[1] * current_position[0]

            self.last_position = current_position

    def update_transform(self):
        glPushMatrix()
        glLoadIdentity()
        glRotated(self.angle, self.axis[0], self.axis[1], self.axis[2])
        glMultMatrixd(self.trackball_x_form, 0)
        glGetDoublev(GL_MODELVIEW_MATRIX, self.trackball_x_form, 0)
        glPopMatrix()
        self.rotating = False


class Ellipse2D:
    x: float
    y: float
    width: float
    height: float

    def __init__(self, x: float = .0, y: float = .0, width: float = .0, height: float = .0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, x: float, y: float) -> bool:
        rx = self.width / 2
        ry = self.height / 2
        tx = (x - (self.x + rx)) / rx
        ty = (y - (self.y + ry)) / ry
        return tx * tx + ty * ty < 1.0

    def get_center_x(self) -> float:
        return self.get_center()[0]

    def get_center_y(self) -> float:
        return self.get_center()[1]

    def get_center(self) -> (float, float):
        return self.x + self.width / 2.0, self.y + self.height / 2.0
