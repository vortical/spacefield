
import asyncio
import math
from datetime import datetime, timezone

from astropy import units as u
from astropy.time import Time as AstroTime
from astroquery.jplhorizons import Horizons

from spacefield.model.bodies import Vector, Ephemeris, TrajectoryPoint, MissionWindow


#
# def _query_horizons(naif_id: int, jd: float) -> Ephemeris:
#     obj = Horizons(id=str(naif_id), location='@0', epochs=jd)
#     v = obj.vectors(refplane='frame')[0]
#     return Ephemeris(
#         position=Vector(
#             x=float((v['x'] * u.au).to(u.m).value),
#             y=float((v['y'] * u.au).to(u.m).value),
#             z=float((v['z'] * u.au).to(u.m).value),
#         ),
#         velocity=Vector(
#             x=float((v['vx'] * u.au / u.day).to(u.m / u.s).value),
#             y=float((v['vy'] * u.au / u.day).to(u.m / u.s).value),
#             z=float((v['vz'] * u.au / u.day).to(u.m / u.s).value),
#         ),
#     )

def _fetch_trajectory(naif_id: int, start: datetime, end: datetime = None) -> list[TrajectoryPoint]:
    """Fetch full trajectory from Horizons at 1-minute resolution. Returns ICRF positions (m) and velocities (m/s)."""

    # Horizons' vectors() API interprets the epochs start/stop string as TDB.
    # Convert the caller's UTC window into TDB calendar representation so that
    # Horizons samples at the physical instant the caller asked for.



    # Horizons returns Julian dates in TDB (Barycentric Dynamical Time).
    # We must declare scale='tdb' so the conversion to UTC accounts for the
    # TDB–UTC offset (~69 s). These UTC datetimes are then passed to Skyfield
    # (which converts back to TDB internally), keeping spacecraft and body
    # positions evaluated at the same physical instant.

    # @see https://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html#date-formats
    # JPL Horizons puts somewhat strict guidelines on the date formats: individual epochs have to
    # be provided as Julian dates, whereas epoch ranges have to be provided as ISO dates
    # (YYYY-MM-DD HH-MM UT). If you have your epoch dates in one of these formats but
    # you need the other format, make use of astropy.time.Time for the conversion.

    def calculate_step(start: datetime, end: datetime, max_lines: int = 90000) -> str:
        duration_minutes = (end - start).total_seconds() / 60

        if duration_minutes <= max_lines:
            return '1m'

        # Calculate minimum step in minutes to stay under limit
        min_step_minutes = math.ceil(duration_minutes / max_lines)

        # Round up to a clean interval
        if min_step_minutes <= 1:
            return '1m'
        elif min_step_minutes <= 2:
            return '2m'
        elif min_step_minutes <= 5:
            return '5m'
        elif min_step_minutes <= 10:
            return '10m'
        elif min_step_minutes <= 15:
            return '15m'
        elif min_step_minutes <= 30:
            return '30m'
        elif min_step_minutes <= 60:
            return '1h'
        elif min_step_minutes <= 360:
            return '6h'
        else:
            return '1d'

    if end is None:
        start_jd: float = AstroTime(start.astimezone(timezone.utc)).tdb.jd
        obj = Horizons(id=str(naif_id), location='@0', epochs=start_jd)
    else:
        step = calculate_step(start, end)
        start_iso = AstroTime(start.astimezone(timezone.utc)).tdb.iso
        end_iso = AstroTime(end.astimezone(timezone.utc)).tdb.iso
        obj = Horizons(id=str(naif_id), location='@0', epochs={'start': start_iso, 'stop':end_iso, 'step': step})


    vectors = obj.vectors(refplane='frame')



    points = []
    for row in vectors:
        # Horizons returns JDs in TDB; convert to UTC for consistency with Skyfield
        t = AstroTime(float(row['datetime_jd']), format='jd', scale='tdb').utc.to_datetime(timezone.utc)
        points.append(TrajectoryPoint(
            datetime=t,
            position=[
                float((row['x'] * u.au).to(u.m).value),
                float((row['y'] * u.au).to(u.m).value),
                float((row['z'] * u.au).to(u.m).value),
            ],
            velocity=[
                float((row['vx'] * u.au / u.day).to(u.m / u.s).value),
                float((row['vy'] * u.au / u.day).to(u.m / u.s).value),
                float((row['vz'] * u.au / u.day).to(u.m / u.s).value),
            ],
        ))
    return points

async def get_trajectory_at_time(naif_id: int, start: datetime, end: datetime) -> list[TrajectoryPoint]:
    return await asyncio.to_thread(_fetch_trajectory, naif_id, start, end)


async def get_ephemeris_at_time(naif_id: int, time: datetime) -> Ephemeris:
    """Query JPL Horizons for SSB/ICRF position+velocity of a body at the given time."""
    # Horizons ephemerides are parameterized in TDB (Barycentric Dynamical Time),
    # so we must convert our UTC input to a TDB Julian date for the query.
    # TDB–UTC is around 69 s; omitting the conversion causes ~2000 km position errors.

    # jd = Time(time.astimezone(timezone.utc)).tdb.jd
    # jd = AstroTime(time.astimezone(timezone.utc)).tdb


    trajectories =  await asyncio.to_thread(_fetch_trajectory, naif_id, time)
    row = trajectories[0]

    return Ephemeris(
        position=Vector(
            x=row.position[0],
            y=row.position[1],
            z=row.position[2],
        ),
        velocity=Vector(
            x=row.velocity[0],
            y=row.velocity[1],
            z=row.velocity[2],
        ),
    )


async def get_mission_window(naif_id: int) -> MissionWindow:
    """Query JPL Horizons for the actual available data range for a spacecraft."""

    def do_query():
        # Horizons accepts a very wide date range — it will clamp to what's available
        # and return an error or empty result outside the valid window.
        # We binary-search the boundaries by probing with known-wide ranges.

        # Step 1: try a single epoch near the known start to confirm data exists
        # Step 2: probe backwards for start, forwards for end

        # Simplest reliable approach: query with a very wide window at coarse step,
        # then read the actual first and last returned epochs.

        try:
            obj = Horizons(
                id=str(naif_id),
                location='@0',
                epochs={
                    'start': '1950-01-01',
                    'stop': '2050-01-01',
                    'step': '1y'  # coarse step — we just want boundary epochs
                }
            )
            vectors = obj.vectors(refplane='frame')
        except Exception as e:
            raise RuntimeError(f"Horizons query failed for NAIF ID {naif_id}: {e}")

        if len(vectors) == 0:
            raise RuntimeError(f"No data returned from Horizons for NAIF ID {naif_id}")

        # Horizons returns Julian dates in the 'datetime_jd' column (TDB scale)
        first_jd = float(vectors['datetime_jd'][0])
        last_jd = float(vectors['datetime_jd'][-1])

        start_time = AstroTime(first_jd, format='jd', scale='tdb').utc.to_datetime(timezone.utc)
        end_time = AstroTime(last_jd, format='jd', scale='tdb').utc.to_datetime(timezone.utc)

        return MissionWindow(start=start_time, end=end_time)

    return await asyncio.to_thread(do_query)