from datetime import datetime

from skyfield import api, earthlib
from skyfield.positionlib import position_of_radec

from spacefield.kernels.orientation_provider import OrientationProvider
from spacefield.model.bodies import Vector, Axis
from spacefield.common.geometry import unit

timescale = api.load.timescale()

class EarthOrientationProvider(OrientationProvider):
    def get_axis_at_time(self, name, time: datetime) -> Axis:
        rotation_angle = earthlib.earth_rotation_angle(timescale.from_datetime(time).ut1) * 360
        axis_direction = position_of_radec(ra_hours=0.0, dec_degrees=90.0).position.au
        return Axis(rotation=rotation_angle, direction=Vector.from_array(unit(axis_direction)), z=axis_direction)
