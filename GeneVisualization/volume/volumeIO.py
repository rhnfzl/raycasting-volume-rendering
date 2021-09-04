import io
import os
import itk
import re
import struct
import numpy as np
from abc import ABC, abstractmethod


class VolumeIO:
    def __init__(self, path):
        filename, file_extension = os.path.splitext(path)

        if file_extension == ".fld":
            reader = FLDReader(path)
        else:
            reader = ITKReader(path)

        reader.read()

        self.data = reader.data
        self.dim_x = reader.dim_x
        self.dim_y = reader.dim_y
        self.dim_z = reader.dim_z


class Reader(ABC):
    def __init__(self, path):
        self.path = path
        self.dim_x = 0
        self.dim_y = 0
        self.dim_z = 0
        self.data = None

    def read(self):
        dim_x, dim_y, dim_z, data = self.read_file(self.path)
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.dim_z = dim_z
        self.data = data

    @abstractmethod
    def read_file(self, path):
        pass


class FLDReader(Reader):
    def read_file(self, path):
        dim_x = 0
        dim_y = 0
        dim_z = 0
        data_type = -1
        with open(path, "rb") as file:
            magic_code = file.read(16)
            if len(magic_code) == 16:
                header_text = magic_code.decode()
                if header_text != "# AVS field file":
                    raise Exception("not a valid file")

            file.seek(0)
            header_length = 1
            byte = file.read(1)
            while byte != b'\f':
                header_length = header_length + 1
                byte = file.read(1)

            # skip also next ^L
            header_length = header_length + 1
            file.seek(0)

            h = file.read(header_length)
            if len(h) == header_length:
                header = h.decode()
                dim_x, dim_y, dim_z, data_type = FLDReader.parse_header(header)

            byte_count = dim_x * dim_y * dim_z * data_type
            d = file.read(byte_count)

            if data_type == 1:
                count = len(d)
                data = struct.unpack('B' * count, d)
            elif data_type == 2:
                count = int(len(d) / 2)
                data = struct.unpack('H' * count, d)
            else:
                raise Exception("Only data types 1 and 2 supported")

            return dim_x, dim_y, dim_z, np.array(data).reshape((dim_x, dim_y, dim_z), order="F")

    @staticmethod
    def parse_header(header):
        avs_keys = ["ndim", "dim1", "dim2", "dim3", "nspace", "veclen",
                    "data", "field", "min_ext", "max_ext", "variable", "#", "label", "unit",
                    "min_val", "max_val"]

        dim_x = 0
        dim_y = 0
        dim_z = 0
        data_type = -1
        for token in header.split('\n'):
            if token.find("=") > 0:
                tokens = re.compile("\s*=\s*|\s*#\s*").split(token)
                for avs_index, avs_key in enumerate(avs_keys):
                    if tokens[0] == avs_key:
                        if avs_index == 0:
                            if int(tokens[1]) != 3:
                                raise Exception("Only 3D files supported")
                        elif avs_index == 1:
                            dim_x = int(tokens[1])
                        elif avs_index == 2:
                            dim_y = int(tokens[1])
                        elif avs_index == 3:
                            dim_z = int(tokens[1])
                        elif avs_index == 5:
                            if int(tokens[1]) != 1:
                                raise Exception("Only scalar data are supported")
                        elif avs_index == 6:
                            if tokens[1] == "byte":
                                data_type = 1
                            elif tokens[1] == "short":
                                data_type = 2

                            if data_type < 0:
                                raise Exception("Data type not recognized")
                        elif avs_index == 7:
                            if tokens[1] != "uniform":
                                raise Exception("Only uniform data are supported")

        return dim_x, dim_y, dim_z, data_type


class ITKReader(Reader):
    def read_file(self, path):
        image = itk.imread(path, itk.F)
        data = itk.array_from_image(image)  # type: np.ndarray
        data = data.astype(np.int)
        dim_x, dim_y, dim_z = data.shape

        return dim_x, dim_y, dim_z, data
