import numpy as np
import pandas as pd
import random
from genevis.render import RaycastRenderer
from genevis.transfer_function import TFColor
from genevis.transfer_function import TransferFunction
from volume.volume import GradientVolume, Volume
from collections.abc import ValuesView
import math

"""
structures = pd.read_csv('../meta/structures.csv')
structures.index = structures.database_id
colour_table = pd.concat(
    [structures.color.str.slice(0, 2), structures.color.str.slice(2, 4), structures.color.str.slice(4, 6)],
    axis=1)
colour_table.columns = ["r", "g", "b"]
colour_table = colour_table.apply(lambda col: col.apply(int, base=16), axis=0)
colour_table = colour_table / 255  # Normalize the data
colour_table = colour_table.append(pd.Series([0, 0, 0], name=0, index=['r', 'g', 'b']))  # Add black

"""

# TODO: Implement trilinear interpolation
def trilinear_interpol(volume: Volume, x: float, y: float, z: float):
    xf = int(math.floor(x))
    xc = int(math.ceil(x))
    if (xc >= volume.dim_x):
        print()
        xc = volume.dim_x - 1
    yf = int(math.floor(y))
    yc = int(math.ceil(y))
    if (yc >= volume.dim_y):
        yc = volume.dim_y - 1
    zf = int(math.floor(z))
    zc = int(math.ceil(z))
    if (zc >= volume.dim_z):
        zc = volume.dim_z - 1

    S000 = volume.data[xf, yf, zf]
    S001 = volume.data[xf, yf, zc]
    S010 = volume.data[xf, yc, zf]
    S011 = volume.data[xf, yc, zc]
    S100 = volume.data[xc, yf, zf]
    S101 = volume.data[xc, yf, zc]
    S110 = volume.data[xc, yc, zf]
    S111 = volume.data[xc, yc, zc]

    # alpha: float, beta: float, gamma: float
    alpha= (x - xf)
    beta= (y - yf)
    gamma= (z - zf)

    SX = (1-alpha)*(1-beta)*(1-gamma)*S000 + alpha*(1-beta)*(1-gamma)*S100 + (1-alpha)*beta*(1-gamma)*S010 + alpha*beta*(1-gamma)*S110 + (1-alpha)*(1-beta)*gamma*S001 + alpha*(1-beta)*gamma*S101 + (1-alpha)*beta*gamma*S011 + alpha*beta*gamma*S111

    return SX

def get_voxel(volume: Volume, x: float, y: float, z: float):
    """
    Retrieves the value of a voxel for the given coordinates.
    :param volume: Volume from which the voxel will be retrieved.
    :param x: X coordinate of the voxel
    :param y: Y coordinate of the voxel
    :param z: Z coordinate of the voxel
    :return: Voxel value
    """
    if x < 0 or y < 0 or z < 0 or x >= volume.dim_x or y >= volume.dim_y or z >= volume.dim_z:
        return 0

    x = int(math.floor(x))
    y = int(math.floor(y))
    z = int(math.floor(z))

    return volume.data[x, y, z]

def jugaad_LUT(sed):
    """
    color = []
    for i in range(num):
        color.append([random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)])
    return color
    """
    random.seed(sed)
    return [random.randint(1, 255), random.randint(1, 255), random.randint(1, 255)]

def mip_voxel(volume: Volume, x: float, y: float, z: float):
    """
    Retrieves the value of a voxel for the given coordinates.
    :param volume: Volume from which the voxel will be retrieved.
    :param x: X coordinate of the voxel
    :param y: Y coordinate of the voxel
    :param z: Z coordinate of the voxel
    :return: Voxel value
    """
    if x < 0 or y < 0 or z < 0 or x >= volume.dim_x or y >= volume.dim_y or z >= volume.dim_z:
        return 0


    return trilinear_interpol(volume, x, y, z)

class RaycastRendererImplementation(RaycastRenderer):
    """
    Class to be implemented.
    """

    def clear_image(self):
        """Clears the image data"""
        self.image.fill(0)

    # TODO: Implement trilinear interpolation
    def render_slicer(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):

        # Clear the image
        self.clear_image()

        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        # Define a step size to make the loop faster
        step = 2 if self.interactive_mode else 1

        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                # Get the voxel coordinate X
                voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                     volume_center[0]

                # Get the voxel coordinate Y
                voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                     volume_center[1]

                # Get the voxel coordinate Z
                voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                     volume_center[2]

                # Get voxel value
                value = get_voxel(volume, voxel_coordinate_x, voxel_coordinate_y, voxel_coordinate_z)

                # Normalize value to be between 0 and 1
                red = value / volume_maximum
                green = red
                blue = red
                alpha = 1.0 if red > 0 else 0.0

                # Compute the color value (0...255)
                red = math.floor(red * 255) if red < 255 else 255
                green = math.floor(green * 255) if green < 255 else 255
                blue = math.floor(blue * 255) if blue < 255 else 255
                alpha = math.floor(alpha * 255) if alpha < 255 else 255

                # Assign color to the pixel i, j
                image[(j * image_size + i) * 4] = red
                image[(j * image_size + i) * 4 + 1] = green
                image[(j * image_size + i) * 4 + 2] = blue
                image[(j * image_size + i) * 4 + 3] = alpha

    # TODO: Implement MIP function
    def render_mip(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        # Clear the image
        self.clear_image()

        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        # Define a step size to make the loop faster
        step = 50 if self.interactive_mode else 1
        #step= 3

        maximumDim = volume.dim_x
        if (volume.dim_y > maximumDim):
            maximumDim = volume.dim_y

        if (volume.dim_z > maximumDim):
            maximumDim = volume.dim_z

        threshold = 0.75 * volume_maximum

        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                maxVoxel = 0
                for k in range(0, maximumDim, 50):
                    # Get the voxel coordinate X
                    voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                         view_vector[0]* k + volume_center[0]

                    # Get the voxel coordinate Y
                    voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                         view_vector[1]* k + volume_center[1]

                    # Get the voxel coordinate Z
                    voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                         view_vector[2]* k + volume_center[2]

                    v = mip_voxel(volume, voxel_coordinate_x, voxel_coordinate_y, voxel_coordinate_z)
                    if (v > maxVoxel):
                        maxVoxel = v

                    if (maxVoxel > threshold):
                        break

                # Get voxel value
                value= maxVoxel

                # Normalize value to be between 0 and 1
                red = value / volume_maximum
                green = red
                blue = red
                alpha = 1.0 if red > 0 else 0.0

                # Compute the color value (0...255)
                red = math.floor(red * 255) if red < 255 else 255
                green = math.floor(green * 255) if green < 255 else 255
                blue = math.floor(blue * 255) if blue < 255 else 255
                alpha = math.floor(alpha * 255) if alpha < 255 else 255

                # Assign color to the pixel i, j
                image[(j * image_size + i) * 4] = red
                image[(j * image_size + i) * 4 + 1] = green
                image[(j * image_size + i) * 4 + 2] = blue
                image[(j * image_size + i) * 4 + 3] = alpha
        pass

    # TODO: Implement Compositing function. TFColor is already imported. self.tfunc is the current transfer function.
    def render_compositing(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        # Clear the image
        self.clear_image()

        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        # Define a step size to make the loop faster
        step = 2 if self.interactive_mode else 1

        maximumDim = volume.dim_x
        if (volume.dim_y > maximumDim):
            maximumDim = volume.dim_y

        if (volume.dim_z > maximumDim):
            maximumDim = volume.dim_z

        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                compTransparancy = 1
                voxel_color= TFColor()
                for k in range(image_size, 0, -50):        # switched the order in loop
                    # Get the voxel coordinate X
                    voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                         view_vector[0]* k + volume_center[0]

                    # Get the voxel coordinate Y
                    voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                         view_vector[1]* k + volume_center[1]

                    # Get the voxel coordinate Z
                    voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                         view_vector[2]* k + volume_center[2]

                    v = get_voxel(volume, voxel_coordinate_x, voxel_coordinate_y, voxel_coordinate_z)

                    sample_color = self.tfunc.get_color(math.floor(v))
                    if sample_color!= []:
                        voxel_color.r = sample_color.a * sample_color.r + (1 - sample_color.a) * voxel_color.r
                        voxel_color.g = sample_color.a * sample_color.g + (1 - sample_color.a) * voxel_color.g
                        voxel_color.b = sample_color.a * sample_color.b + (1 - sample_color.a) * voxel_color.b
                        voxel_color.a = sample_color.a * sample_color.a + (1 - sample_color.a) * voxel_color.a

                        compTransparancy = compTransparancy * (1 - sample_color.a)
                        if (compTransparancy < 0.15):           #make it 0.05
                            break

                # Compute the color value (0...255)
                red = math.floor(voxel_color.r * 255) if voxel_color.r <= 1 else 255
                green = math.floor(voxel_color.g * 255) if voxel_color.g <= 1 else 255
                blue = math.floor(voxel_color.b * 255) if voxel_color.b <= 1 else 255
                alpha = math.floor(voxel_color.a * 255) if voxel_color.a <= 1 else 255

                # Assign color to the pixel i, j
                image[(j * image_size + i) * 4] = red
                image[(j * image_size + i) * 4 + 1] = green
                image[(j * image_size + i) * 4 + 2] = blue
                image[(j * image_size + i) * 4 + 3] = alpha
        pass

    def render_phong(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        L = np.array(view_vector)

        # Define a step size to make the loop faster
        step = 2 if self.interactive_mode else 1

        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                vec_k = np.arange(-100, 100, 1)
                x_k = vec_k * view_vector[0]
                y_k = vec_k * view_vector[1]
                z_k = vec_k * view_vector[2]

                # Get the voxel coordinate X
                voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                     volume_center[0]

                # Get the voxel coordinate Y
                voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                     volume_center[1]

                # Get the voxel coordinate Z
                voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                     volume_center[2]

                vc_vec_x = voxel_coordinate_x + x_k
                vc_vec_y = voxel_coordinate_y + y_k
                vc_vec_z = voxel_coordinate_z + z_k

                N = np.zeros(3)
                found = False

                for k in range(0, image_size, 50):
                    vx = get_voxel(volume, vc_vec_x[k], vc_vec_y[k], vc_vec_z[k])
                    if vx > 1:
                        found = True
                        delta_f = self.annotation_gradient_volume.get_gradient(vc_vec_x[k], vc_vec_y[k], vc_vec_z[k])
                        magnitude_f = delta_f.magnitude
                        N[0] = delta_f.x / magnitude_f
                        N[1] = delta_f.y / magnitude_f
                        N[2] = delta_f.z / magnitude_f
                        break

                # Normalize value to be between 0 and 1
                if found:
                    shadow = (np.dot(N.reshape(1, 3), L) + 1) / 2
                else:
                    shadow = 0

                if shadow < 220:
                    image[(j * image_size + i) * 4] *= shadow
                    image[(j * image_size + i) * 4 + 1] *= shadow
                    image[(j * image_size + i) * 4 + 2] *= shadow
                    image[(j * image_size + i) * 4 + 3] = 255


    # TODO: Implement function to render multiple energy volumes and annotation volume as a silhouette.
    def render_mouse_brain(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                           image_size: int, image: np.ndarray):
        self.render_mip(view_matrix, annotation_volume, image_size, image)
        #self.render_mouse_compositing(view_matrix, annotation_volume, image_size, image)
        #self.render_phong(view_matrix, annotation_volume, image_size, image)
        # TODO: Implement your code considering these volumes (annotation_volume, and energy_volumes)
        for i in energy_volumes:
            self.render_mip(view_matrix, energy_volumes[i], image_size, image)
            #self.render_mouse_compositing(view_matrix, energy_volumes[i], image_size, image)
            #self.render_phong(view_matrix, energy_volumes[i], image_size, image)
        pass

    def render_mouse_brain_colour(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                           image_size: int, image: np.ndarray):
        self.render_my_mouse(view_matrix, annotation_volume, image_size, image, -1)
        # TODO: Implement your code considering these volumes (annotation_volume, and energy_volumes)
        for i in energy_volumes:
            self.render_my_mouse(view_matrix, energy_volumes[i], image_size, image, i)
        pass

    def render_mouse_brain_phong(self, view_matrix: np.ndarray, annotation_volume: Volume, energy_volumes: dict,
                           image_size: int, image: np.ndarray):
        self.render_mip(view_matrix, annotation_volume, image_size, image)
        self.render_phong(view_matrix, annotation_volume, image_size, image)
        # TODO: Implement your code considering these volumes (annotation_volume, and energy_volumes)
        for i in energy_volumes:
            self.render_mip(view_matrix, energy_volumes[i], image_size, image)
            self.render_phong(view_matrix, energy_volumes[i], image_size, image)
        pass

    def render_my_mouse(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray, runner:int):
        # Clear the image
        self.clear_image()


        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        # Define a step size to make the loop faster
        step = 40 if self.interactive_mode else 1
        # step= 3

        maximumDim = volume.dim_x
        if (volume.dim_y > maximumDim):
            maximumDim = volume.dim_y

        if (volume.dim_z > maximumDim):
            maximumDim = volume.dim_z

        threshold = 0.75 * volume_maximum

        color = jugaad_LUT(runner)
        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                maxVoxel = 0
                for k in range(0, maximumDim, 50):
                    # Get the voxel coordinate X
                    voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                         view_vector[0] * k + volume_center[0]

                    # Get the voxel coordinate Y
                    voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                         view_vector[1] * k + volume_center[1]

                    # Get the voxel coordinate Z
                    voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                         view_vector[2] * k + volume_center[2]

                    v = mip_voxel(volume, voxel_coordinate_x, voxel_coordinate_y, voxel_coordinate_z)
                    if (v > maxVoxel):
                        maxVoxel = v

                    if (maxVoxel > threshold):
                        break

                # Get voxel value
                value = maxVoxel

                # Normalize value to be between 0 and 1
                red = value / volume_maximum
                alpha = 1.0 if red > 0 else 0.0

                alpha = math.floor(alpha * 255) if alpha < 255 else 255

                # Assign color to the pixel i, j
                image[(j * image_size + i) * 4] = color[0]
                image[(j * image_size + i) * 4 + 1] = color[1]
                image[(j * image_size + i) * 4 + 2] = color[2]
                image[(j * image_size + i) * 4 + 3] = alpha
        pass

    def render_mouse_compositing(self, view_matrix: np.ndarray, volume: Volume, image_size: int, image: np.ndarray):
        # Clear the image
        self.clear_image()

        # U vector. See documentation in parent's class
        u_vector = view_matrix[0:3]

        # V vector. See documentation in parent's class
        v_vector = view_matrix[4:7]

        # View vector. See documentation in parent's class
        view_vector = view_matrix[8:11]

        # Center of the image. Image is squared
        image_center = image_size / 2

        # Center of the volume (3-dimensional)
        volume_center = [volume.dim_x / 2, volume.dim_y / 2, volume.dim_z / 2]
        volume_maximum = volume.get_maximum()

        # Define a step size to make the loop faster
        step = 2 if self.interactive_mode else 1

        maximumDim = volume.dim_x
        if (volume.dim_y > maximumDim):
            maximumDim = volume.dim_y

        if (volume.dim_z > maximumDim):
            maximumDim = volume.dim_z

        for i in range(0, image_size, step):
            for j in range(0, image_size, step):
                compTransparancy = 1
                voxel_color= TFColor()
                for k in range(image_size, 0, -50):        # switched the order in loop
                    # Get the voxel coordinate X
                    voxel_coordinate_x = u_vector[0] * (i - image_center) + v_vector[0] * (j - image_center) + \
                                         view_vector[0]* k + volume_center[0]

                    # Get the voxel coordinate Y
                    voxel_coordinate_y = u_vector[1] * (i - image_center) + v_vector[1] * (j - image_center) + \
                                         view_vector[1]* k + volume_center[1]

                    # Get the voxel coordinate Z
                    voxel_coordinate_z = u_vector[2] * (i - image_center) + v_vector[2] * (j - image_center) + \
                                         view_vector[2]* k + volume_center[2]

                    v = get_voxel(volume, voxel_coordinate_x, voxel_coordinate_y, voxel_coordinate_z)

                    sample_color = self.tfunc.get_color(math.floor(v))
                    if sample_color!= []:
                        voxel_color.r = sample_color.a * sample_color.r + (1 - sample_color.a) * voxel_color.r
                        voxel_color.g = sample_color.a * sample_color.g + (1 - sample_color.a) * voxel_color.g
                        voxel_color.b = sample_color.a * sample_color.b + (1 - sample_color.a) * voxel_color.b
                        voxel_color.a = sample_color.a * sample_color.a + (1 - sample_color.a) * voxel_color.a

                        compTransparancy = compTransparancy * (1 - sample_color.a)
                        if (compTransparancy < 0.15):           #make it 0.05
                            break

                # Compute the color value (0...255)
                red = math.floor(voxel_color.r * 255) if voxel_color.r <= 1 else 255
                green = math.floor(voxel_color.g * 255) if voxel_color.g <= 1 else 255
                blue = math.floor(voxel_color.b * 255) if voxel_color.b <= 1 else 255
                alpha = math.floor(voxel_color.a * 255) if voxel_color.a <= 1 else 255

                # Assign color to the pixel i, j
                image[(j * image_size + i) * 4] = red
                image[(j * image_size + i) * 4 + 1] = green
                image[(j * image_size + i) * 4 + 2] = blue
                image[(j * image_size + i) * 4 + 3] = alpha
        pass

class GradientVolumeImpl(GradientVolume):
    # TODO: Implement gradient compute function. See parent class to check available attributes.
    def compute(self):
        pass
