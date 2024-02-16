
from datetime import datetime, timezone

import numpy as np
from skyfield import api, earthlib
from skyfield.api import load
from skyfield.positionlib import position_of_radec
from spacefield.model.bodies import BarycentricEntry, Vector, Axis

data_directory = '/spacefield/data'
loader = api.Loader(data_directory)

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


def axis(body_name, time) -> Axis | None:
    """
    Only earth for now...
    This will require using tpc kernels etc...

    :param body_name:
    :param time:
    :return:
    """

    if body_name.lower() != "earth":
        return None

    #
    # So for now just return data for earth.

    rotation_angle = earthlib.earth_rotation_angle(time.ut1) * 360

    # this is pretty much [0,0,1] for earth given the reference frame is ICRF
    axis_direction = position_of_radec(ra_hours=0.0, dec_degrees=90.0).position.au
    # unit vector
    axis_direction = axis_direction / np.linalg.norm(axis_direction)
    return Axis(rotation=rotation_angle, direction=Vector.from_array(axis_direction))


def position(body_name, time: datetime):
    body = get_body(body_name)
    skyfieldTime = timescale.from_datetime(time)
    body_at_time = body.at(skyfieldTime)
    return BarycentricEntry(name=body_name,
                            axis=axis(body_name, skyfieldTime),
                            position=Vector.from_array(body_at_time.position.m),
                            velocity=Vector.from_array(body_at_time.velocity.m_per_s),
                            datetime=body_at_time.t.utc_datetime())

