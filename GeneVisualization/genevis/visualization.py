from util import TrackballInteractor
from implementation import RaycastRendererImplementation
import wx

try:
    from wx import glcanvas
except ImportError:
    raise Exception("Problem when importing glcanvas. Is PyOpenGL available?")

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
except ImportError:
    raise Exception("PyOpenGL is not installed. Use pip install")


class Visualization(glcanvas.GLCanvas):
    """ Visualization class that implements the necessary methods for painting in a OpenGL Canvas."""

    def __init__(self, parent, tfunc):
        """
        Sets up the class with the right attributes.
        :param parent: Parent WX component to be added to.
        """

        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        self.context = glcanvas.GLContext(self)

        self.last_x = self.x = 30
        self.last_y = self.y = 30
        self.size = None
        self.mouse_down = False
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        parent.Bind(wx.EVT_SIZE, self.on_reshape)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

        self.winWidth = 800
        self.winHeight = 600
        self.fov = 20.0
        self.trackball = TrackballInteractor(self.winWidth, self.winHeight)
        self.renderer = RaycastRendererImplementation(tfunc)

        self.energy_volumes = {}
        self.annotation_volume = None

    def set_volume(self, volume):
        """
        Convenient method to set the volume that we want to render
        :param volume: Volume to be set (see `~volume.Volume`)
        """

        self.renderer.set_volume(volume)
        self.Refresh(False)

    def add_energy_volume(self, key, volume):
        self.renderer.add_energy_volume(key, volume)
        self.Refresh(False)

    def remove_energy_volume(self, key):
        self.renderer.remove_energy_volume(key)
        self.Refresh(False)

    def clear_energy_volumes(self):
        self.renderer.clear_energy_volumes()
        self.Refresh(False)

    def set_annotation_volume(self, volume):
        self.renderer.set_annotation_volume(volume)
        self.Refresh(False)

    def set_mode(self, mode):
        self.renderer.set_mode(mode)
        self.Refresh(False)

    def on_erase_background(self, event):
        pass  # Do nothing, to avoid flashing on MSW.

    def on_reshape(self, event):
        """Handler for the reshape event"""

        wx.CallAfter(self.do_set_viewport)
        event.Skip()

    def do_set_viewport(self):
        """Set the viewport correctly"""

        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        glViewport(0, 0, size.width, size.height)
        self.renderer.winWidth = size.width
        self.renderer.winHeight = size.height

        self.winWidth = size.width
        self.winHeight = size.height
        self.trackball.set_dimensions(size.width, size.height)
        self.Refresh(False)

    def on_paint(self, event):
        """
        Handler for paint event. It includes the logic to deal with WX and the OpenGL logic to draw the visualization.
        """
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.winWidth / self.winHeight, 0.1, 5000)
        glTranslated(0, 0, -1000)

        # clear screen and set the view transform to the identity matrix
        glClearColor(0, 0, .0, .0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        if self.trackball.rotating:
            self.trackball.update_transform()

        glMultMatrixd(self.trackball.get_transformation_matrix(), 0)

        self.renderer.visualize()
        glFlush()
        self.SwapBuffers()

    def on_mouse_down(self, evt):
        """Handler for mouse down event"""

        self.mouse_down = True
        self.CaptureMouse()
        x, y = evt.GetPosition()
        self.trackball.set_mouse_position(x, y)
        self.renderer.interactive_mode = True

    def on_mouse_up(self, evt):
        """Handler for mouse up event"""

        self.mouse_down = False
        self.ReleaseMouse()
        self.renderer.interactive_mode = False
        self.Refresh(False)

    def on_mouse_motion(self, evt):
        """Handler for mouse motion event"""

        if evt.Dragging() and self.mouse_down:
            x, y = evt.GetPosition()
            self.trackball.drag(x, y)
            self.trackball.rotating = True
            self.Refresh(False)

    def on_mouse_wheel(self, evt):
        """Handler for mouse wheel event"""

        if evt.GetWheelRotation() > 0:
            self.fov = self.fov - 1
            if self.fov < 2:
                self.fov = 2
        else:
            self.fov = self.fov + 1
        self.Refresh(False)
