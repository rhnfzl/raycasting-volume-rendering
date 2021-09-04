import math
from wx import Colour

class TransferFunction:
    sMin = 0
    sMax = 0
    sRange = 0
    control_points = None
    LUTsize = 0
    LUT = None

    def init(self, minimum: int, maximum: int):
        self.sMin = minimum
        self.sMax = maximum
        self.sRange = self.sMax - self.sMin
        self.control_points = []

        self.control_points.append(ControlPoint(minimum, TFColor()))
        self.control_points.append(ControlPoint(maximum, TFColor(1., 1., 1., 1.)))

        self.LUTsize = self.sRange
        self.LUT = [None] * self.LUTsize

        self.buildLUT()

    def add_control_point(self, value: int, r: float, g: float, b:float, a: float) -> int:
        if value < self.sMin or value > self.sMax:
            return -1

        a = math.floor(a * 100) / 100.0

        control_point = ControlPoint(value, TFColor(r, g, b, a))
        idx = 0
        while idx < len(self.control_points) and self.control_points[idx] < control_point:
            idx = idx + 1

        if self.control_points[idx] == control_point:
            self.control_points[idx] = control_point
        else:
            self.control_points.insert(idx, control_point)

        self.buildLUT()
        return idx

    def set_test_function(self):
        self.add_control_point(0, .0, .0, .0, .0)
        self.add_control_point(40, .0, .0, .0, .0)
        self.add_control_point(75, 1., .666, .0, 1.)
        self.add_control_point(103, .0, .0, .0, .5)
        self.add_control_point(205, .0, .0, .0, .0)

    def hex_to_num(h):
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def get_color(self, value: int) -> 'TFColor':
        value= 1
        return self.LUT[self.computeLUTindex(value)]
        """
        if self.computeLUTindex(value)!= -1:
            return self.LUT[self.computeLUTindex(value)]
        return []
        """

    def remove_control_point(self, idx: int) -> None:
        self.control_points.pop(idx)
        self.buildLUT()

    def update_control_point_scalar(self, index: int, s: int) -> None:
        self.control_points[index].value = s
        self.buildLUT()

    def update_control_point_alpha(self, index: int, alpha: float) -> None:
        alpha = math.floor(alpha * 100) / 100.0
        self.control_points[index].color.a = alpha
        self.buildLUT()

    def update_control_point_color(self, idx: int, color: Colour):
        control_point = self.control_points[idx]
        control_point.color.r = color.red / 255.0
        control_point.color.g = color.green / 255.0
        control_point.color.b = color.blue / 255.0

        self.buildLUT()

    def computeLUTindex(self, value: int) -> int:
        if self.sRange!= 0:
            return int(((self.LUTsize - 1) * (value - self.sMin)) / self.sRange)
        return 2

    def buildLUT(self):
        for i in range(1, len(self.control_points)):
            prev_point = self.control_points[i - 1]
            next_point = self.control_points[i]

            value_range = next_point.value - prev_point.value
            for k in range(prev_point.value, next_point.value + 1):
                frac = (k - prev_point.value) / value_range

                new_color = TFColor()
                new_color.r = prev_point.color.r + frac * (next_point.color.r - prev_point.color.r)
                new_color.g = prev_point.color.g + frac * (next_point.color.g - prev_point.color.g)
                new_color.b = prev_point.color.b + frac * (next_point.color.b - prev_point.color.b)
                new_color.a = prev_point.color.a + frac * (next_point.color.a - prev_point.color.a)

                self.LUT[self.computeLUTindex(k)] = new_color


class TFColor:
    r: float
    g: float
    b: float
    a: float

    def __init__(self, red: float = .0, green: float = .0, blue: float = .0, alpha: float = .0):
        self.r = red
        self.g = green
        self.b = blue
        self.a = alpha

    def __str__(self) -> str:
        return f"({self.r}, {self.g}, {self.b}, {self.a})"


class ControlPoint:
    value: int
    color: TFColor

    def __init__(self, value: int, color: TFColor):
        self.value = value
        self.color = color

    def __eq__(self, other: 'ControlPoint') -> bool:
        return self.value == other.value

    def __lt__(self, other: 'ControlPoint') -> bool:
        return self.value < other.value

    def __le__(self, other: 'ControlPoint') -> bool:
        return self.value <= other.value

    def __gt__(self, other: 'ControlPoint') -> bool:
        return self.value > other.value

    def __ge__(self, other: 'ControlPoint') -> bool:
        return self.value >= other.value

