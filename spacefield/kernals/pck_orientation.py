from datetime import datetime
from typing import Optional

from kernals.orientation_provider import OrientationProvider
from spacefield.common.geometry import to_cartesian
from spacefield.model.bodies import Axis, Polar, Vector
from spacefield.time.intervals import julian_centuries_interval, days_interval

# https://astropedia.astrogeology.usgs.gov/download/Docs/WGCCRE/WGCCRE2009reprint.pdf
# This data is also available in pck0000[8-11].tpc

_poles = {
    'sun': {
        'pole_ra': (286.13, 0, 0),
        'pole_dec': (63.87, 0, 0),
        'pm': (84.176, 14.18440, 0)
    },
    'mercury': {
        'pole_ra': (281.0097, -0.0328, 0),
        'pole_dec': (61.4143, -0.0049, 0),
        'pm': (329.5469, 6.1385025, 0)
    },
    'venus': {
        'pole_ra': (272.76, 0, 0),
        'pole_dec': (67.16, 0, 0),
        'pm': (160.20, -1.4813688, 0)
    },
    'mars': {
        'pole_ra': (317.68143, -0.1061, 0),
        'pole_dec': (52.88650, -0.0609, 0),
        'pm': (176.630, 350.89198226, 0)
    },
    'jupiter': {
        'pole_ra': (268.056595, -0.006499, 0),
        'pole_dec': (64.495303, 0.002413, 0),
        'pm': (284.95, 870.5360000, 0)
    },
    'saturn': {
        'pole_ra': (40.589, -0.036, 0),
        'pole_dec': (83.537, -0.004, 0),
        'pm': (38.90, 810.7939024, 0)
    },
    'uranus': {
        'pole_ra': (257.311, 0, 0),
        'pole_dec': (-15.175, 0, 0),
        'pm': (203.81, -501.1600928, 0)
    },
    'neptune': {
        'pole_ra': (299.36, 0, 0),
        'pole_dec': (43.46, 0, 0),
        'pm': (253.18, 536.3128492, 0)
    },
    'pluto': {
        'pole_ra': (132.993, 0, 0),
        'pole_dec': (-6.163, 0, 0),
        'pm': (302.695, 56.3625225, 0)
    },
    'puck': {
        'pole_ra': (257.31, 0, 0),
        'pole_dec': (-15.18, 0, 0),
        'pm': (91.24, - 472.5450690, 0)
    },
    'phobos': {
        'pole_ra': (317.68, -0.108, 0),
        'pole_dec': (52.90, -0.061, 0),
        'pm': (35.06, 1128.8445850, 0)
    },
    'deimos': {
        'pole_ra': (316.65, -0.108, 0),
        'pole_dec': (53.52, -0.061, 0),
        'pm': (79.41, 285.1618970, 0)
    }
}


def get_polar_axis(pck_data, time: datetime):
    return Polar(ra=pck_data['pole_ra'][0] + pck_data['pole_ra'][1] * julian_centuries_interval(time),
                 dec=pck_data['pole_dec'][0] + pck_data['pole_dec'][1] * julian_centuries_interval(time),
                 pm=(pck_data['pm'][0] + pck_data['pm'][1] * days_interval(time)) % 360)


class PCKOrientationProvider(OrientationProvider):

    def __init__(self, pck_poles=None):
        if pck_poles is None:
            pck_poles = _poles
        self.pck_poles = pck_poles

    def get_axis_at_time(self, name, time: datetime) -> Optional[Axis]:
        pck_data = self.pck_poles.get(str(name).lower())
        if pck_data is None:
            return None

        polar_axis = get_polar_axis(pck_data, time)
        (x, y, z) = to_cartesian(polar_axis.ra, polar_axis.dec)
        return Axis(rotation=polar_axis.pm, direction=Vector(x=x, y=y, z=z), z=(x, y, z))
