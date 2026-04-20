
import re
from datetime import datetime, timezone

import numpy as np
from astropy import units as u
from astropy.time import Time
from astroquery.jplhorizons import Horizons

from spacefield.config import GM_KERNEL_PATH
from spacefield.kernels.ephemeris import BodyEphemerisKernel
from spacefield.model.bodies import BurnEvent, Ephemeris, MissionWindow, TrajectoryPoint, Vector

# NAIF body IDs included in gravity model
_GRAVITY_BODIES = {
    10:  "sun",
    399: "earth",
    301: "moon",
    2:   "venus barycenter",
    4:   "mars barycenter",
    5:   "jupiter barycenter",
}

_KM3_S2_TO_M3_S2 = (1 * u.km ** 3 / u.s ** 2).to(u.m ** 3 / u.s ** 2).value

_BURN_THRESHOLD_M_S2 = 0.02  # residual acceleration above this → burn
_STEP_SECONDS = 60

# J2 oblateness parameters for close-approach bodies
_J2_BODIES = {
    399: {  # Earth
        'j2': 1.08263e-3,
        'r_eq': 6_378_137.0,  # metres
        'pole': np.array([0.0, 0.0, 1.0]),  # ICRF ≈ Earth equatorial at J2000
    },
    301: {  # Moon
        'j2': 2.033e-4,
        'r_eq': 1_738_100.0,  # metres
        'pole': np.array([0.0, -0.3978, 0.9175]),  # Moon pole in ICRF (RA~270°, Dec~66.5°)
    },
}


def _load_gm_kernel(path: str = GM_KERNEL_PATH) -> dict[int, float]:
    """Parse gm_de440.tpc, return {naif_id: gm_m3_s2}."""
    gm = {}
    pattern = re.compile(r'BODY(\d+)_GM\s*=\s*\(\s*([\d.EDed+\-]+)\s*\)')
    with open(path) as f:
        for line in f:
            m = pattern.search(line)
            if m:
                body_id = int(m.group(1))
                value = float(m.group(2).replace('D', 'E').replace('d', 'e'))
                gm[body_id] = value * _KM3_S2_TO_M3_S2
    return gm


def _j2_accel(r_rel: np.ndarray, dist: float, gm: float,
              j2: float, r_eq: float, pole: np.ndarray) -> np.ndarray:
    """J2 oblateness perturbation acceleration (m/s²)."""
    s = np.dot(r_rel, pole)
    factor = -1.5 * j2 * gm * r_eq ** 2 / dist ** 5
    return factor * ((5 * s ** 2 / dist ** 2 - 1) * r_rel - 2 * s * pole)


def _gravity_accel(r_sc: np.ndarray, time: datetime, gm: dict[int, float],
                   kernel: BodyEphemerisKernel) -> np.ndarray:
    """Total gravitational acceleration (m/s²) on spacecraft at position r_sc (m)."""
    accel = np.zeros(3)
    for body_id, body_name in _GRAVITY_BODIES.items():
        gm_val = gm.get(body_id)
        if gm_val is None:
            continue
        eph = kernel.get_ephemeris_at_time(body_name, time)
        if eph is None:
            continue
        r_body = np.array([eph.position.x, eph.position.y, eph.position.z])
        diff = r_body - r_sc
        dist = np.linalg.norm(diff)
        if dist > 0:
            accel += gm_val * diff / dist ** 3
            if body_id in _J2_BODIES:
                params = _J2_BODIES[body_id]
                accel += _j2_accel(diff, dist, gm_val, params['j2'], params['r_eq'], params['pole'])
    return accel


def analyze_trajectory(naif_id: int, window: MissionWindow) -> tuple[list[BurnEvent], MissionWindow]:
    """Fetch trajectory from Horizons, detect burns, and derive the actual mission window."""
    gm = _load_gm_kernel()
    kernel = BodyEphemerisKernel()

    start = window.start.strftime("%Y-%m-%d %H:%M:%S")
    stop = window.end.strftime("%Y-%m-%d %H:%M:%S")

    obj = Horizons(id=str(naif_id), location='@0',
                   epochs={'start': start, 'stop': stop, 'step': '1m'})
    vectors = obj.vectors(refplane='frame')

    # Horizons returns Julian dates in TDB (Barycentric Dynamical Time).
    # We must declare scale='tdb' so the conversion to UTC accounts for the
    # TDB–UTC offset (~69 s). These UTC datetimes are then passed to Skyfield
    # (which converts back to TDB internally), keeping spacecraft and body
    # positions evaluated at the same physical instant.
    times = [Time(float(row['datetime_jd']), format='jd', scale='tdb').utc.to_datetime(timezone.utc)
             for row in vectors]
    positions = np.array([[float(r['x']), float(r['y']), float(r['z'])]
                          for r in vectors]) * (1 * u.au).to(u.m).value
    velocities = np.array([[float(r['vx']), float(r['vy']), float(r['vz'])]
                           for r in vectors]) * (1 * u.au / u.day).to(u.m / u.s).value

    n = len(times)
    residuals = np.zeros((n, 3))

    for i in range(1, n - 1):
        a_actual = (velocities[i + 1] - velocities[i - 1]) / (2 * _STEP_SECONDS)
        a_grav = _gravity_accel(positions[i], times[i], gm, kernel)
        residuals[i] = a_actual - a_grav

    burns = []
    in_burn = False
    burn_start_idx = 0

    for i in range(n):
        above = np.linalg.norm(residuals[i]) > _BURN_THRESHOLD_M_S2
        if above and not in_burn:
            in_burn = True
            burn_start_idx = i
        elif not above and in_burn:
            in_burn = False
            if i - 1 > burn_start_idx:  # require at least 2 samples
                burns.append(_make_burn_event(times, residuals, burn_start_idx, i - 1))

    if in_burn and n - 2 > burn_start_idx:
        burns.append(_make_burn_event(times, residuals, burn_start_idx, n - 2))

    burns = [b for b in burns if b.mean_acceleration_m_s2 >= _BURN_THRESHOLD_M_S2]

    actual_window = MissionWindow(start=times[0], end=times[-1])
    return burns, actual_window


def _make_burn_event(times, residuals, start_idx: int, end_idx: int) -> BurnEvent:
    burn_residuals = residuals[start_idx:end_idx + 1]  # shape (k, 3), m/s²
    mean_vector = np.mean(burn_residuals, axis=0)
    mean_accel = float(np.linalg.norm(mean_vector))
    magnitudes = np.linalg.norm(burn_residuals, axis=1)
    total_dv = float(np.sum(magnitudes) * _STEP_SECONDS)
    duration = (times[end_idx] - times[start_idx]).total_seconds()

    return BurnEvent(
        start=times[start_idx],
        end=times[end_idx],
        duration_s=duration,
        burn_vector=Vector(x=float(mean_vector[0]), y=float(mean_vector[1]), z=float(mean_vector[2])),
        total_delta_v_m_s=total_dv,
        mean_acceleration_m_s2=mean_accel,
    )


def fetch_trajectory(naif_id: int, window: MissionWindow) -> list[TrajectoryPoint]:
    """Fetch full trajectory from Horizons at 1-minute resolution. Returns ICRF positions (m) and velocities (m/s)."""
    start = window.start.strftime("%Y-%m-%d %H:%M:%S")
    stop = window.end.strftime("%Y-%m-%d %H:%M:%S")

    obj = Horizons(id=str(naif_id), location='@0',
                   epochs={'start': start, 'stop': stop, 'step': '1m'})
    vectors = obj.vectors(refplane='frame')

    au_to_m = (1 * u.au).to(u.m).value
    au_day_to_m_s = (1 * u.au / u.day).to(u.m / u.s).value

    points = []
    for row in vectors:
        # Horizons returns JDs in TDB; convert to UTC for consistency with Skyfield
        t = Time(float(row['datetime_jd']), format='jd', scale='tdb').utc.to_datetime(timezone.utc)
        points.append(TrajectoryPoint(
            datetime=t,
            ephemeris=Ephemeris(
                position=Vector(
                    x=float(row['x']) * au_to_m,
                    y=float(row['y']) * au_to_m,
                    z=float(row['z']) * au_to_m,
                ),
                velocity=Vector(
                    x=float(row['vx']) * au_day_to_m_s,
                    y=float(row['vy']) * au_day_to_m_s,
                    z=float(row['vz']) * au_day_to_m_s,
                ),
            ),
        ))
    return points
