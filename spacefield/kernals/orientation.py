
from abc import ABC, abstractmethod

from datetime import datetime, timezone

from kernals.earth_orientation import EarthOrientationProvider
from kernals.moon_orientation import MoonOrientationProvider
from kernals.orientation_provider import OrientationProvider
from kernals.pck_orientation import PCKOrientationProvider
from model.bodies import Axis


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
        return orientation_provider.orientation(body_name, time)
