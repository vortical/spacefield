
import asyncio
from datetime import datetime, timezone

from astropy.time import Time
from astroquery.jplhorizons import Horizons

from spacefield.model.bodies import Vector, Ephemeris

_AU_TO_M = 149597870700.0
_AU_PER_DAY_TO_M_PER_S = _AU_TO_M / 86400.0


def _query_horizons(naif_id: int, jd: float) -> Ephemeris:
    obj = Horizons(id=str(naif_id), location='@0', epochs=jd)
    v = obj.vectors()[0]
    return Ephemeris(
        position=Vector(
            x=float(v['x']) * _AU_TO_M,
            y=float(v['y']) * _AU_TO_M,
            z=float(v['z']) * _AU_TO_M,
        ),
        velocity=Vector(
            x=float(v['vx']) * _AU_PER_DAY_TO_M_PER_S,
            y=float(v['vy']) * _AU_PER_DAY_TO_M_PER_S,
            z=float(v['vz']) * _AU_PER_DAY_TO_M_PER_S,
        ),
    )


async def get_horizons_state(naif_id: int, time: datetime) -> Ephemeris:
    """Query JPL Horizons for SSB/ICRF position+velocity of a body at the given time."""
    jd = Time(time.astimezone(timezone.utc)).jd
    return await asyncio.to_thread(_query_horizons, naif_id, jd)
