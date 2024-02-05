
from datetime import datetime, timezone

from skyfield import api
from skyfield.api import load

from spacefield.model.bodies import BarycentricEntry, Vector

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
    kernel_files = kernel_mappings.get(str(body_name))

    if not kernel_files:
        raise Exception(f"Unknown body: {body_name}")

    kernel = loader(kernel_files[0])
    return kernel[body_name]



def position(body_name, time: datetime):
    body = get_body(body_name)
    body_at_time = body.at(timescale.from_datetime(time))
    return BarycentricEntry(name=body_name,
                            position=Vector.from_array(body_at_time.position.m),
                            velocity=Vector.from_array(body_at_time.velocity.m_per_s),
                            datetime=body_at_time.t.utc_datetime());

