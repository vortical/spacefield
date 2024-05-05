
from datetime import datetime
import numpy as np
import math

from skyfield import api
from skyfield.api import PlanetaryConstants
from skyfield.functions import mxv

from spacefield.kernels.orientation_provider import OrientationProvider
from spacefield.common.geometry import circular_angle
from spacefield.model.bodies import Vector, Axis

data_directory = '/spacefield/data'
loader = api.Loader(data_directory)

pc = PlanetaryConstants()
pc.read_text(loader('moon_080317.tf'))
pc.read_text(loader('pck00008.tpc'))
pc.read_binary(loader('moon_pa_de421_1900-2050.bpc'))

moon_frame = pc.build_frame_named('MOON_ME_DE421')

timescale = api.load.timescale()

def frame_axis(time: datetime, frame) -> Axis | None:
    rotation_to_frame = frame.rotation_at(timescale.from_datetime(time))
    rotation_from_frame = rotation_to_frame.T

    z = mxv(rotation_from_frame, np.array([0, 0, 1]))
    x = mxv(rotation_from_frame, np.array([1, 0, 0]))
    rotation_angle = circular_angle(np.array([1, 0, 0]), x, z) * 180 / math.pi
    return Axis(rotation=rotation_angle, direction=Vector.from_array(z), x=x, y=np.cross(x, z), z=z)


class MoonOrientationProvider(OrientationProvider):
    def get_axis_at_time(self, name, time: datetime) -> Axis:
        return frame_axis(time, moon_frame)
