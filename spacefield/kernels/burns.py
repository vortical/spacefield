import asyncio
import re
from datetime import datetime, timedelta, timezone

import numpy as np
from astropy import units as u
from astropy.time import Time
from astroquery.jplhorizons import Horizons

from spacefield.config import GM_KERNEL_PATH
from spacefield.kernels.ephemeris import BodyEphemerisKernel
from spacefield.model.bodies import BurnAcceleration, BurnEvent, MissionWindow, TrajectoryPoint, Vector
from astropy.time import Time as AstroTime

import spacefield.kernels.horizons as horizons

# NAIF body IDs included in gravity model
_GRAVITY_BODIES = {
    10:  "sun",
    399: "earth",
    301: "moon",
    1:   "mercury barycenter",
    2:   "venus barycenter",
    4:   "mars barycenter",
    5:   "jupiter barycenter",
    6:   "saturn barycenter",
}

_KM3_S2_TO_M3_S2 = (1 * u.km ** 3 / u.s ** 2).to(u.m ** 3 / u.s ** 2).value

_BURN_THRESHOLD_M_S2 = 0.005  # residual acceleration above this → burn
MIN_DELTA_V_M_S = 0.1
MIN_EFFICIENCY = 0.15
_STEP_SECONDS = 60 # our trajectory points are for every 60 seconds.



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


def _gravity_accel(r_spacecraft: np.ndarray, time: datetime, gm: dict[int, float], kernel: BodyEphemerisKernel) -> np.ndarray:
    """Total gravitational acceleration (m/s²) on spacecraft at position r_sc (m)."""
    accel = np.zeros(3)
    for body_id, body_name in _GRAVITY_BODIES.items():
        gm_val = gm.get(body_id)
        if gm_val is None:
            raise RuntimeError(f"Failed to retrieve gm valu Cae for {body_name}")

        eph = kernel.get_ephemeris_at_time(body_name, time)
        if eph is None:
            raise RuntimeError(f"Failed to retrieve ephemeris for {body_name}")

        r_body = np.array([eph.position.x, eph.position.y, eph.position.z])
        diff = r_body - r_spacecraft
        dist = np.linalg.norm(diff)
        if dist > 0:
            accel += gm_val * diff / dist ** 3

    return accel


def _make_burn_event(times, d_v: np.ndarray, s: int, e: int) -> BurnEvent:
    n_intervals = e - s + 1

    # Each minute's constant acceleration is simply d_v[k] / dt.
    # With sub-second simulator timesteps, the rectangle rule accumulates
    # exactly d_v[k] over the full 60-second interval
    accelerations_out = d_v[s:e + 1] / _STEP_SECONDS  # shape (n_intervals, 3)

    start_time = times[s]
    end_time = times[e] + timedelta(seconds=_STEP_SECONDS)

    net_dv = np.sum(d_v[s:e + 1], axis=0)
    burn_dv_total = float(np.linalg.norm(net_dv))
    gross_dv = float(np.sum(np.linalg.norm(d_v[s:e + 1], axis=1)))
    efficiency = burn_dv_total / gross_dv if gross_dv > 0 else 0.0
    burn_vector = net_dv / burn_dv_total
    mean_accel = burn_dv_total / (n_intervals * _STEP_SECONDS)

    accelerations = [
        BurnAcceleration(
            datetime=times[s + k],
            acceleration=accelerations_out[k].tolist(),
        )
        for k in range(n_intervals)
    ]

    return BurnEvent(
        start=start_time,
        end=end_time,
        duration_s=n_intervals * _STEP_SECONDS,
        burn_vector=Vector(x=float(burn_vector[0]), y=float(burn_vector[1]), z=float(burn_vector[2])),
        total_delta_v_m_s=burn_dv_total,
        mean_acceleration_m_s2=mean_accel,
        efficiency=efficiency,
        accelerations=accelerations,
    )


async def analyze_trajectory(trajectory_points: list[TrajectoryPoint]) -> list[BurnEvent]:
    """Fetch trajectory from Horizons, detect burns, and derive the actual mission window."""
    def do_analyze():
        gm = _load_gm_kernel()
        kernel = BodyEphemerisKernel()


        # Horizons returns Julian dates in TDB (Barycentric Dynamical Time).
        # We must declare scale='tdb' so the conversion to UTC accounts for the
        # TDB–UTC offset (~69 s). These UTC datetimes are then passed to Skyfield
        # (which converts back to TDB internally), keeping spacecraft and body
        # positions evaluated at the same physical instant.



        times = [row.datetime for row in trajectory_points]
        positions = np.array([row.position for row in trajectory_points])
        velocities = np.array([row.velocity for row in trajectory_points])

        n_points = len(times)
        gravity_accelerations = np.array([_gravity_accel(positions[i], times[i], gm, kernel) for i in range(n_points)])

        # d_v[i] is the non-gravitational velocity change centred on t_i,
        # estimated via central difference over [t_{i-1}, t_{i+1}].
        # d_v[0] and d_v[n-2] remain zero (no thrust assumed at boundaries).
        d_v = np.zeros((n_points - 1, 3))
        for i in range(1 , n_points - 1):
            a_total = (velocities[i + 1] - velocities[i-1]) / (2 *_STEP_SECONDS)
            # a_gravity = 0.5 * (gravity_accelerations[i-1] + gravity_accelerations[i + 1])
            a_gravity = gravity_accelerations[i]  # at current point, not averaged neighbours
            d_v[i] = (a_total - a_gravity) * _STEP_SECONDS

        burns = []
        in_burn = False
        burn_start_idx = 0
        consecutive_accelerations = 0

        for i in range(n_points - 1):
            is_above_threshold = (np.linalg.norm(d_v[i]) / _STEP_SECONDS) > _BURN_THRESHOLD_M_S2
            if is_above_threshold and not in_burn:
                consecutive_accelerations += 1
                if consecutive_accelerations == 1:
                    burn_start_idx = i
                elif consecutive_accelerations >= 2:
                    in_burn = True

            elif not is_above_threshold and in_burn:
                in_burn = False
                consecutive_accelerations = 0
                burns.append(_make_burn_event(times, d_v, burn_start_idx, i - 1))
            elif not is_above_threshold and not in_burn:
                consecutive_accelerations = 0

        # close last burn if there was one started
        if in_burn:
            burns.append(_make_burn_event(times, d_v, burn_start_idx, n_points - 2))


        return [b for b in burns if b.total_delta_v_m_s >= MIN_DELTA_V_M_S and b.efficiency >= MIN_EFFICIENCY]


    return await asyncio.to_thread(do_analyze)

