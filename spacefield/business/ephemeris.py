from datetime import datetime, timezone

from spacefield.kernals.ephemeris import BodyEphemerisKernel
from spacefield.kernals.orientation import BodyOrientationKernel
from spacefield.model.bodies import BarycentricEntry

ephemerisKernel = BodyEphemerisKernel()
orientationKernel = BodyOrientationKernel()

def position(body_name, time: datetime):
    ephemeris = ephemerisKernel.get_ephemeris_at_time(body_name, time)
    orientation = orientationKernel.get_axis_at_time(body_name, time)

    return BarycentricEntry(name=body_name,
                            axis=orientation,
                            ephemeris=ephemeris,
                            datetime=time.astimezone(timezone.utc))
