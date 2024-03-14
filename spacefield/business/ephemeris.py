
from datetime import datetime, timezone

import numpy as np
from skyfield import api, earthlib
from skyfield.api import load, PlanetaryConstants
from skyfield.positionlib import position_of_radec
from skyfield.functions import mxv, length_of
from spacefield.model.bodies import BarycentricEntry, Vector, Axis
from skyfield.functions import angle_between, mxv
import math

data_directory = '/spacefield/data'
loader = api.Loader(data_directory)


pc = PlanetaryConstants()
pc.read_text(load('moon_080317.tf'))
pc.read_text(load('pck00008.tpc'))
pc.read_binary(load('moon_pa_de421_1900-2050.bpc'))

frame = pc.build_frame_named('MOON_ME_DE421')

kernel_files = dict(
    planets="de440s.bsp",
    mars="e_mar097.bsp",
    jupiter="e_jup365.bsp",
    saturn="e_sat441.bsp",
    neptune="e_nep095.bsp",
    uranus="e_ura111.bsp",
    # pluto="e_plu058.bsp"
    pluto="plu043.bsp"
)
def build_kernel_mappings():
    """
    Given some bodies (.e.g. the sun) can have entries in multiple bsp files, then
    :return: a map of body name -> kernel (.bsf) files
    """
    map = dict()

    for file_name in kernel_files.values():
        kernel = loader(file_name)
        for names in kernel.names().values():
            for name in names:
                name = name.lower()
                file_names = map.get(name, [])
                file_names.append(file_name)
                map[name] = file_names
    return map


kernel_mappings = build_kernel_mappings()
timescale = api.load.timescale()

def get_names() -> list[str]:
    # return list("one")
    return list(kernel_mappings)

def get_body(body_name):
    kernel_files = kernel_mappings.get(str(body_name).lower())

    if not kernel_files:
        raise Exception(f"Unknown body: {body_name}")

    kernel = loader(kernel_files[0])
    return kernel[body_name]



def moon_axis(time) -> Axis | None:
    top = pc.build_latlon_degrees(frame, 90, 0)
    bottom = pc.build_latlon_degrees(frame, -90, 0)
    meridian = pc.build_latlon_degrees(frame, 0, 0)

    top_at = top.at(time)
    bottom_at = bottom.at(time)
    meridian_at = meridian.at(time)

    axis_unit = unit((top_at - bottom_at).position.m)
    meridian_unit = unit(meridian_at.position.m)
    rotation_angle = circular_angle(np.array([1, 0, 0]), meridian_unit, axis_unit) * 180 / math.pi

    return Axis(rotation=rotation_angle, direction=Vector.from_array(axis_unit))



def unit(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def projection(u, n):
    """
    given u = v + (projection of u onto n), then
    v = u - (projection of u onto n)
    which is what we want.
    :param u: vector
    :param n: normal to plan
    :return: projection of u onto plane with normal n
    """
    #      u - (projection of u onto n)
    return u - np.dot(u,n)/np.dot(n, n) * n



def circular_angle(v1, v2, plane_normal=np.array([0,0,1])):
    """

    :param v1:
    :param v2:
    :param plane_normal:
    :return: An angle between 0 and 2PI (not PI), in the direction of the normal.
    """
    v1_p = projection(v1, plane_normal)
    v2_p = projection(v2, plane_normal)

    a = angle_between(v1_p, v2_p)

    if angle_between(np.cross(v1_p, v2_p), plane_normal) < math.pi/2:
        return a
    else:
        return math.pi * 2 - a

def unit(v: np.array) -> np.array:
    return v / np.linalg.norm(v)

def axis(body_name, time) -> Axis | None:
    """
    Only earth for now...
    This will require using tpc kernels etc...

    :param body_name:
    :param time:
    :return:
    """

    if body_name.lower() == "earth":
        rotation_angle = earthlib.earth_rotation_angle(time.ut1) * 360
        # this is pretty much [0,0,1] for earth given the reference frame is ICRF
        axis_direction = position_of_radec(ra_hours=0.0, dec_degrees=90.0).position.au
        return Axis(rotation=rotation_angle, direction=Vector.from_array(unit(axis_direction)))
    elif body_name.lower() == "moon":
        # rotation_angle = None
        # axis_direction = moon_axis(time)
        return moon_axis(time) #Axis(rotation=None, direction=Vector.from_array(unit(axis_direction)))
    else:
        return None



def position(body_name, time: datetime):
    body = get_body(body_name)
    skyfieldTime = timescale.from_datetime(time)
    body_at_time = body.at(skyfieldTime)
    return BarycentricEntry(name=body_name,
                            axis=axis(body_name, skyfieldTime),
                            position=Vector.from_array(body_at_time.position.m),
                            velocity=Vector.from_array(body_at_time.velocity.m_per_s),
                            datetime=body_at_time.t.utc_datetime())

