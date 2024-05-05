from spacefield.kernels.earth_orientation import EarthOrientationProvider
from spacefield.kernels.moon_orientation import MoonOrientationProvider
from spacefield.kernels.orientation_provider import OrientationProvider
from spacefield.kernels.pck_orientation import PCKOrientationProvider
from spacefield.model.bodies import Axis


earth_orientation_provider = EarthOrientationProvider()
moon_orientation_provider = MoonOrientationProvider()
pck_orientation_provider = PCKOrientationProvider()

def get_orientation_provider(name):
    match name.lower():
        case "earth":
            return earth_orientation_provider
        case "moon":
            return moon_orientation_provider
        case _:
            return pck_orientation_provider

class BodyOrientationKernel(OrientationProvider):
    def get_axis_at_time(self, body_name, time) -> Axis | None:
        orientation_provider = get_orientation_provider(body_name)
        return orientation_provider.get_axis_at_time(body_name, time)
