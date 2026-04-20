
import asyncio
from datetime import datetime, timezone

from astropy import units as u
from astropy.time import Time
from astroquery.jplhorizons import Horizons

from spacefield.model.bodies import Vector, Ephemeris


def _query_horizons(naif_id: int, jd: float) -> Ephemeris:
    obj = Horizons(id=str(naif_id), location='@0', epochs=jd)
    v = obj.vectors(refplane='frame')[0]
    return Ephemeris(
        position=Vector(
            x=float((v['x'] * u.au).to(u.m).value),
            y=float((v['y'] * u.au).to(u.m).value),
            z=float((v['z'] * u.au).to(u.m).value),
        ),
        velocity=Vector(
            x=float((v['vx'] * u.au / u.day).to(u.m / u.s).value),
            y=float((v['vy'] * u.au / u.day).to(u.m / u.s).value),
            z=float((v['vz'] * u.au / u.day).to(u.m / u.s).value),
        ),
    )


async def get_horizons_state(naif_id: int, time: datetime) -> Ephemeris:
    """Query JPL Horizons for SSB/ICRF position+velocity of a body at the given time."""
    # Horizons ephemerides are parameterized in TDB (Barycentric Dynamical Time),
    # so we must convert our UTC input to a TDB Julian date for the query.
    # TDB–UTC ≈ 69 s; omitting the conversion causes ~2000 km position errors.
    jd = Time(time.astimezone(timezone.utc)).tdb.jd
    return await asyncio.to_thread(_query_horizons, naif_id, jd)
