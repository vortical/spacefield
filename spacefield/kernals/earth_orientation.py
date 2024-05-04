from datetime import datetime
from skyfield import api, earthlib
# from skyfield.api import PlanetaryConstants
from skyfield.positionlib import position_of_radec

from kernals.orientation_provider import OrientationProvider
from spacefield.model.bodies import Vector, Axis
from spacefield.math.geometry import unit

# data_directory = '/spacefield/data'
# loader = api.Loader(data_directory)
# pc = PlanetaryConstants()
# pc.read_text(loader('moon_080317.tf'))
# pc.read_text(loader('pck00008.tpc'))
# pc.read_binary(loader('moon_pa_de421_1900-2050.bpc'))
#
# moon_frame = pc.build_frame_named('MOON_ME_DE421')

timescale = api.load.timescale()

class EarthOrientationProvider(OrientationProvider):
    def get_axis_at_time(self, name, time: datetime) -> Axis:
        rotation_angle = earthlib.earth_rotation_angle(timescale.from_datetime(time).ut1) * 360
        axis_direction = position_of_radec(ra_hours=0.0, dec_degrees=90.0).position.au
        return Axis(rotation=rotation_angle, direction=Vector.from_array(unit(axis_direction)))
