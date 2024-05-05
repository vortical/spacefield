from datetime import datetime, timezone
from typing import List, Optional

from spacefield.kernals.ephemeris import BodyEphemerisKernel
from spacefield.kernals.orientation import BodyOrientationKernel
from spacefield.model.bodies import BarycentricState

ephemerisKernel = BodyEphemerisKernel()
orientationKernel = BodyOrientationKernel()


def get_names() -> List[str]:
    return ephemerisKernel.get_names()


def get_state(body_name, time: datetime) -> Optional[BarycentricState]:
    ephemeris = ephemerisKernel.get_ephemeris_at_time(body_name, time)

    if ephemeris is None:
        return None

    orientation = orientationKernel.get_axis_at_time(body_name, time)

    return BarycentricState(name=body_name,
                            axis=orientation,
                            ephemeris=ephemeris,
                            datetime=time.astimezone(timezone.utc))
