
from datetime import datetime, timezone

from typing import List, Mapping, Sequence, Optional

from skyfield import api, earthlib

from spacefield.model.bodies import Vector, Ephemeris

data_directory = '/spacefield/data'
loader = api.Loader(data_directory)
timescale = api.load.timescale()
_default_kernel_files = (
    "de440s.bsp",
    "e_mar097.bsp",
    "e_jup365.bsp",
    "e_sat441.bsp",
    "e_nep095.bsp",
    "ura111.bsp",
    "ura115.bsp",
    "plu043.bsp"
)

def _build_kernel_mappings(kernel_files: Sequence[str]) -> Mapping[str, List[str]]:
    """
    Given some bodies (.e.g. the sun) can have entries in multiple bsp files, then
    :return: a map of body name -> kernel (.bsf) files
    """
    map = dict()

    for file_name in kernel_files:
        kernel = loader(file_name)
        for names in kernel.names().values():
            for name in names:
                name = name.lower()
                file_names = map.get(name, [])
                file_names.append(file_name)
                map[name] = file_names
    return map

class BodyEphemerisKernel:

    def __init__(self, kernel_files=_default_kernel_files):
        self.kernel_mappings = _build_kernel_mappings(kernel_files)

    def get_names(self) -> list[str]:
        return list(self.kernel_mappings)

    def get_body(self, name) -> Optional[any]:
        kernel_files = self.kernel_mappings.get(str(name).lower())
        return loader(kernel_files[0])[name] if kernel_files else None

    def get_ephemeris_at_time(self, body_name, time: datetime) -> Optional[Ephemeris]:
        body = self.get_body(body_name)
        if not body:
            return None
        body_at_time = body.at(timescale.from_datetime(time))
        return Ephemeris(
            position=Vector.from_array(body_at_time.position.m),
            velocity=Vector.from_array(body_at_time.velocity.m_per_s))

