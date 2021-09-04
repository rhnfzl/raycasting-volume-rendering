from abc import abstractmethod, ABC
from enum import Enum
import numpy as np
import math
from volume.volume import GradientVolume, Volume
import time
from .transfer_function import TransferFunction
from typing import List
from collections.abc import ValuesView

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    from OpenGL.GLU import *
except ImportError:
    raise Exception("PyOpenGL is not installed. Use pip install")


def generate_texture(width: int, height: int) -> int:
    # Generate one texture
    texture_id = glGenTextures(1)
    # Bind the following operations to the generated texture
    glBindTexture(GL_TEXTURE_2D, texture_id)
    # Set some parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    # Reserves space in memory for the given parameters. The space will be filled later on
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

    return texture_id


def draw_bounding_box(volume: Volume):
    """Draws a bounding box around the volume."""
    glPushAttrib(GL_CURRENT_BIT)
    glDisable(GL_LIGHTING)
    glColor4d(1.0, 1.0, 1.0, 1.0)
    glLineWidth(1.5)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glBegin(GL_LINE_LOOP)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glEnd()

    glBegin(GL_LINE_LOOP)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glEnd()

    glBegin(GL_LINE_LOOP)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glEnd()

    glBegin(GL_LINE_LOOP)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glEnd()

    glBegin(GL_LINE_LOOP)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glEnd()

    glBegin(GL_LINE_LOOP)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glVertex3d(-volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, volume.dim_z / 2.0)
    glVertex3d(volume.dim_x / 2.0, -volume.dim_y / 2.0, -volume.dim_z / 2.0)
    glEnd()

    glDisable(GL_LINE_SMOOTH)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)
    glPopAttrib()


class RenderMode(Enum):
    """Enumerate indicating the possible modes of the application."""
    SLICER = 1
    MIP = 2
    COMPOSITING = 3
    MULTI_VOLUME = 4
    COLOR_MULTI= 5
    BRAIN_PHONG= 6



class RaycastRenderer(ABC):
    """
    Abstract RaycastRenderer. It includes the logic needed to render a bounding box and convert image data into a
    texture that can be displayed with OpenGL. Students will have to implement the abstract methods.

    The class calls the appropriate render function based on the chosen mode.

    Attributes:
        volume: The volume that we want to render.
        image_size: The size of the image that represents the volume and will be rendered.
        image: A numpy array with shape (image_size, image_size, 4). Each element must be a ~`numpy.int8`. The last
        dimension represents a 4 channels color (Red, Green, Blue, Alpha) with values between 0 and 255.
        interactive_mode: Boolean indicating whether or not we are in the interactive (rotating) mode.
        view_matrix: Numpy array that will contain the values of the ModelView matrix from OpenGL.
        mode: Mode of the renderer. Can be one from `RendererMode`.
        texture_id: ID of the texture for the Test Volume (Orange, Tomato, etc.)
        tfunc: Transfer Function for the Test Volume (Orange, Tomato, etc.)
        energy_volumes: Dictionary with the energy volumes that user has selected.
        annotation_volume: Annotation volume that has been selected by the user.
        annotation_gradient_volume: Gradient computed over the annotation volume.
        challenge_image_size: Size of the texture for the challenge volume selected by the user.
        challenge_image: Array containing the pixel data for the challenge volume selected by the user.
        challenge_texture_id: Texture id for the challenge volume.
    """

    def __init__(self, tfunc: TransferFunction):
        self.volume = None
        self.image_size = 0
        self.image = np.zeros(0, dtype=np.int8)

        self.winWidth = self.winHeight = 0
        self.interactive_mode = False
        self.view_matrix = np.zeros(16)
        self.mode = RenderMode.SLICER
        self.texture_id = -1
        self.tfunc = tfunc

        self.energy_volumes = {}
        self.annotation_volume = None
        self.annotation_gradient_volume = None
        self.challenge_image_size = 0
        self.challenge_image = np.zeros(0, dtype=np.int8)
        self.challenge_texture_id = -1

    def set_volume(self, volume):
        """Sets the volume to be rendered."""

        self.volume = volume

        self.image_size = math.floor(math.sqrt(
            self.volume.dim_x * self.volume.dim_x + self.volume.dim_y * self.volume.dim_y + self.volume.dim_z * self.volume.dim_z))
        if self.image_size % 2 != 0:
            self.image_size = self.image_size + 1

        self.image = np.zeros(self.image_size * self.image_size * 4, dtype=np.int8)  # image_size x image_size x RGBA

        if self.texture_id != -1:
            glDeleteTextures(1, [self.texture_id])
            self.texture_id = -1

        self.tfunc.set_test_function()

    def add_energy_volume(self, key, volume):
        self.energy_volumes[key] = volume

    def remove_energy_volume(self, key):
        del self.energy_volumes[key]

    def clear_energy_volumes(self):
        self.energy_volumes = {}

    def set_annotation_volume(self, volume):
        self.annotation_volume = volume
        self.annotation_gradient_volume = GradientVolume(volume)
        self.challenge_image_size = math.floor(math.sqrt(
            volume.dim_x * volume.dim_x + volume.dim_y * volume.dim_y + volume.dim_z * volume.dim_z))
        if self.challenge_image_size % 2 != 0:
            self.challenge_image_size = self.challenge_image_size + 1

        self.challenge_image = np.zeros(self.challenge_image_size * self.challenge_image_size * 4,
                                        dtype=np.int8)  # image_size x image_size x RGBA

        if self.challenge_texture_id != -1:
            glDeleteTextures(1, [self.challenge_texture_id])
            self.challenge_texture_id = -1

    def set_mode(self, mode):
        """Convenient method to set renderer's mode."""

        self.mode = mode

    @abstractmethod
    def render_slicer(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        """
        Slicer rendering method. It must be overridden in the subclass.
        :param view_matrix: ModelView OpenGL matrix (`more information <http://www.songho.ca/opengl/gl_transform.html>`).
        :param volume: The volume to be rendered.
        :param image_size: The size of the image.
        :param image: The resulting image. It will be a numpy array with shape (image_size * image_size * 4,)
        representing the pixel RGBA values.
        It represents the model and the view matrices of the current scene TRANSPOSED. It is a 4x4 matrix looking like:
            m_0  m_1  m_2  m_3

            m_4  m_5  m_6  m_7

            m_8  m_9  m_10 m_11

            m_12  m_13  m_14 m_15

        where m_0, m_1 and m_2 represent the 3-dimensional coordinates of the X axis; m_4, m_5 and m_6 represent the
        3-dimensional coordinates of the Y axis; and m_8, m_9 and m_10 represent the 3-dimensional coordinates of the
        Z axis. The other numbers are not interesting for us.
        """
        pass

    @abstractmethod
    def render_mip(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        """
        MIP rendering method. It must be overridden in the subclass.
        :param view_matrix: ModelView OpenGL matrix (`more information <http://www.songho.ca/opengl/gl_transform.html>`).
        :param volume: The volume to be rendered.
        :param image_size: The size of the image.
        :param image: The resulting image. It will be a numpy array with shape (image_size * image_size * 4,)
        representing the pixel RGBA values.
        It represents the model and the view matrices of the current scene TRANSPOSED. It is a 4x4 matrix looking like:
            m_0  m_1  m_2  m_3

            m_4  m_5  m_6  m_7

            m_8  m_9  m_10 m_11

            m_12  m_13  m_14 m_15

        where m_0, m_1 and m_2 represent the 3-dimensional coordinates of the X axis; m_4, m_5 and m_6 represent the
        3-dimensional coordinates of the Y axis; and m_8, m_9 and m_10 represent the 3-dimensional coordinates of the
        Z axis. The other numbers are not interesting for us.
        """
        pass

    @abstractmethod
    def render_compositing(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        """Compositing rendering method. It must be overridden in the subclass.
        :param view_matrix: ModelView OpenGL matrix (`more information <http://www.songho.ca/opengl/gl_transform.html>`).
        :param volume: The volume to be rendered.
        :param image_size: The size of the image.
        :param image: The resulting image. It will be a numpy array with shape (image_size * image_size * 4,)
        representing the pixel RGBA values.
        It represents the model and the view matrices of the current scene TRANSPOSED. It is a 4x4 matrix looking like:
            m_0  m_1  m_2  m_3

            m_4  m_5  m_6  m_7

            m_8  m_9  m_10 m_11

            m_12  m_13  m_14 m_15

        where m_0, m_1 and m_2 represent the 3-dimensional coordinates of the X axis; m_4, m_5 and m_6 represent the
        3-dimensional coordinates of the Y axis; and m_8, m_9 and m_10 represent the 3-dimensional coordinates of the
        Z axis. The other numbers are not interesting for us.
        """
        pass

    @abstractmethod
    def render_mouse_brain(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                           image_size: int, image: np.ndarray):
        """Method to render the mouse brain (challenge data). It must be overridden in the subclass.
        :param view_matrix: ModelView OpenGL matrix (`more information <http://www.songho.ca/opengl/gl_transform.html>`).
        :param annotation_volume: The annotation volume to be rendered.
        :param energy_volumes: Dictionary containing additional volumes indicating the energy of some gene expessions within
        the annotation volume. Those volumes will have the same shape. The keys of the dictonary are integers which
        value depicts a region in the annotated volume. The values are the corresponding energy volumes. E.g.: if we
        load file "100053243_energy.mhd" this dictionar will contain one element with key 100053243 and volume data from
        the aforementioned file.
        :param image_size: The size of the image.
        :param image: The resulting image. It will be a numpy array with shape (image_size * image_size * 4,)
        representing the pixel RGBA values.
        It represents the model and the view matrices of the current scene TRANSPOSED. It is a 4x4 matrix looking like:
            m_0  m_1  m_2  m_3

            m_4  m_5  m_6  m_7

            m_8  m_9  m_10 m_11

            m_12  m_13  m_14 m_15

        where m_0, m_1 and m_2 represent the 3-dimensional coordinates of the X axis; m_4, m_5 and m_6 represent the
        3-dimensional coordinates of the Y axis; and m_8, m_9 and m_10 represent the 3-dimensional coordinates of the
        Z axis. The other numbers are not interesting for us.
        """
        pass

    @abstractmethod
    def render_mouse_brain_colour(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                           image_size: int, image: np.ndarray):

        pass

    @abstractmethod
    def render_mouse_brain_phong(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                                  image_size: int, image: np.ndarray):

        pass

    def visualize(self):
        """
        Convenient method to visualize the volume. It renders the bounding box, retrieves the ViewMatrix from OpenGL,
        and calls the corresponding rendering method (based on ~`self.mode` value), and converts the resulting image
        data into an OpenGL Texture.
        """

        if self.mode == RenderMode.MULTI_VOLUME or self.mode == RenderMode.COLOR_MULTI or self.mode == RenderMode.BRAIN_PHONG:
            if not self.annotation_volume:
                return

            draw_bounding_box(self.annotation_volume)
        else:
            if not self.volume:
                return
            draw_bounding_box(self.volume)

        glGetDoublev(GL_MODELVIEW_MATRIX, self.view_matrix, 0)
        view_matrix_transposed = self.view_matrix.reshape((4, 4)).transpose().flatten()

        start_time = time.time()

        if self.mode == RenderMode.SLICER:
            self.render_slicer(view_matrix_transposed, self.volume, self.image_size, self.image)
        elif self.mode == RenderMode.MIP:
            self.render_mip(view_matrix_transposed, self.volume, self.image_size, self.image)
        elif self.mode == RenderMode.COMPOSITING:
            self.render_compositing(view_matrix_transposed, self.volume, self.image_size, self.image)
        elif self.mode == RenderMode.MULTI_VOLUME:
            self.render_mouse_brain(view_matrix_transposed, self.annotation_volume, self.energy_volumes,
                                    self.challenge_image_size, self.challenge_image)
        elif self.mode == RenderMode.COLOR_MULTI:
            self.render_mouse_brain_colour(view_matrix_transposed, self.annotation_volume, self.energy_volumes,
                                    self.challenge_image_size, self.challenge_image)
        elif self.mode == RenderMode.BRAIN_PHONG:
            self.render_mouse_brain_phong(view_matrix_transposed, self.annotation_volume, self.energy_volumes,
                                    self.challenge_image_size, self.challenge_image)
        else:
            raise Error("Specified mode is not correct")

        end_time = time.time()
        print(f"Render took {end_time - start_time}s")

        # TEXTURE
        if self.mode == RenderMode.MULTI_VOLUME or self.mode == RenderMode.COLOR_MULTI or self.mode == RenderMode.BRAIN_PHONG:
            half_width = self.challenge_image_size / 2.0
        else:
            half_width = self.image_size / 2.0

        if self.texture_id == -1:
            self.texture_id = generate_texture(self.image_size, self.image_size)

        if self.challenge_texture_id == -1:
            self.challenge_texture_id = generate_texture(self.challenge_image_size, self.challenge_image_size)

        glPushAttrib(GL_LIGHTING_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_TEXTURE_2D)  # Enable the GL_TEXTURE_2D

        if self.mode == RenderMode.MULTI_VOLUME or self.mode == RenderMode.COLOR_MULTI or self.mode == RenderMode.BRAIN_PHONG:
            glBindTexture(GL_TEXTURE_2D, self.challenge_texture_id)  # Bind the following operation to the texture
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.challenge_image_size, self.challenge_image_size, GL_RGBA,
                            GL_UNSIGNED_BYTE,
                            self.challenge_image)  # Fill the reserved space with the final image data
        else:
            glBindTexture(GL_TEXTURE_2D, self.texture_id)  # Bind the following operation to the texture
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.image_size, self.image_size, GL_RGBA, GL_UNSIGNED_BYTE,
                            self.image)  # Fill the reserved space with the final image data

        # Actually draw the texture as a billboard texture.
        glPushMatrix()
        glLoadIdentity()
        glBegin(GL_QUADS)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glTexCoord2d(0.0, 0.0)
        glVertex3d(-half_width, -half_width, 0.0)
        glTexCoord2d(0.0, 1.0)
        glVertex3d(-half_width, half_width, 0.0)
        glTexCoord2d(1.0, 1.0)
        glVertex3d(half_width, half_width, 0.0)
        glTexCoord2d(1.0, 0.0)
        glVertex3d(half_width, -half_width, 0.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glPopMatrix()

        glPopAttrib()
