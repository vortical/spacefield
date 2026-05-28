#
# import re
# from datetime import datetime, timedelta, timezone
#
# import numpy as np
# from astropy import units as u
# from astropy.time import Time
# from astroquery.jplhorizons import Horizons
#
# from spacefield.config import GM_KERNEL_PATH
# from spacefield.kernels.ephemeris import BodyEphemerisKernel
# from spacefield.model.bodies import BurnAcceleration, BurnEvent, MissionWindow, TrajectoryPoint, Vector
# from astropy.time import Time as AstroTime
#
# import spacefield.kernels.horizons as horizons
# #
# # # NAIF body IDs included in gravity model
# # _GRAVITY_BODIES = {
# #     10:  "sun",
# #     399: "earth",
# #     301: "moon",
# #     1:   "mercury barycenter",
# #     2:   "venus barycenter",
# #     4:   "mars barycenter",
# #     5:   "jupiter barycenter",
# #     6:   "saturn barycenter",
# # }
# #
# # _KM3_S2_TO_M3_S2 = (1 * u.km ** 3 / u.s ** 2).to(u.m ** 3 / u.s ** 2).value
# #
# # _BURN_THRESHOLD_M_S2 = 0.005  # residual acceleration above this → burn
# # _STEP_SECONDS = 60
# #
# #
# #
# # def _load_gm_kernel(path: str = GM_KERNEL_PATH) -> dict[int, float]:
# #     """Parse gm_de440.tpc, return {naif_id: gm_m3_s2}."""
# #     gm = {}
# #     pattern = re.compile(r'BODY(\d+)_GM\s*=\s*\(\s*([\d.EDed+\-]+)\s*\)')
# #     with open(path) as f:
# #         for line in f:
# #             m = pattern.search(line)
# #             if m:
# #                 body_id = int(m.group(1))
# #                 value = float(m.group(2).replace('D', 'E').replace('d', 'e'))
# #                 gm[body_id] = value * _KM3_S2_TO_M3_S2
# #     return gm
# #
# #
# # def _gravity_accel(r_sc: np.ndarray, time: datetime, gm: dict[int, float],
# #                    kernel: BodyEphemerisKernel) -> np.ndarray:
# #     """Total gravitational acceleration (m/s²) on spacecraft at position r_sc (m)."""
# #     accel = np.zeros(3)
# #     for body_id, body_name in _GRAVITY_BODIES.items():
# #         gm_val = gm.get(body_id)
# #         if gm_val is None:
# #             continue
# #         eph = kernel.get_ephemeris_at_time(body_name, time)
# #         if eph is None:
# #             continue
# #         r_body = np.array([eph.position.x, eph.position.y, eph.position.z])
# #         diff = r_body - r_sc
# #         dist = np.linalg.norm(diff)
# #         if dist > 0:
# #             accel += gm_val * diff / dist ** 3
# #
# #     return accel
# #
# #
# # def analyze_trajectory(naif_id: int, window: MissionWindow) -> tuple[list[BurnEvent], MissionWindow]:
# #     """Fetch trajectory from Horizons, detect burns, and derive the actual mission window."""
# #     gm = _load_gm_kernel()
# #     kernel = BodyEphemerisKernel()
# #
# #     start = window.start.strftime("%Y-%m-%d %H:%M:%S")
# #     stop = window.end.strftime("%Y-%m-%d %H:%M:%S")
# #
# #     obj = Horizons(id=str(naif_id), location='@0',
# #                    epochs={'start': start, 'stop': stop, 'step': '1m'})
# #     vectors = obj.vectors(refplane='frame')
# #
# #     # Horizons returns Julian dates in TDB (Barycentric Dynamical Time).
# #     # We must declare scale='tdb' so the conversion to UTC accounts for the
# #     # TDB–UTC offset (~69 s). These UTC datetimes are then passed to Skyfield
# #     # (which converts back to TDB internally), keeping spacecraft and body
# #     # positions evaluated at the same physical instant.
# #     times = [Time(float(row['datetime_jd']), format='jd', scale='tdb').utc.to_datetime(timezone.utc)
# #              for row in vectors]
# #     positions = np.array([[float(r['x']), float(r['y']), float(r['z'])]
# #                           for r in vectors]) * (1 * u.au).to(u.m).value
# #     velocities = np.array([[float(r['vx']), float(r['vy']), float(r['vz'])]
# #                            for r in vectors]) * (1 * u.au / u.day).to(u.m / u.s).value
# #
# #     n = len(times)
# #     grav_cache = np.array([_gravity_accel(positions[i], times[i], gm, kernel) for i in range(n)])
# #
# #     # Per-interval true burn Δv (m/s). d_v[i] is the velocity change over [t_i, t_{i+1}]
# #     # beyond what the reference gravity model accounts for — i.e., what the client must
# #     # accumulate in minute i (plus the trapezoid-boundary correction applied below).
# #     d_v = np.zeros((n - 1, 3))
# #     for i in range(n - 1):
# #         a_actual = (velocities[i + 1] - velocities[i]) / _STEP_SECONDS
# #         a_grav = 0.5 * (grav_cache[i] + grav_cache[i + 1])
# #         d_v[i] = (a_actual - a_grav) * _STEP_SECONDS
# #
# #     burns = []
# #     in_burn = False
# #     burn_start_idx = 0
# #
# #     for i in range(n - 1):
# #         above = np.linalg.norm(d_v[i]) / _STEP_SECONDS > _BURN_THRESHOLD_M_S2
# #         if above and not in_burn:
# #             in_burn = True
# #             burn_start_idx = i
# #         elif not above and in_burn:
# #             in_burn = False
# #             burns.append(_make_burn_event(times, d_v, burn_start_idx, i - 1))
# #
# #     if in_burn:
# #         burns.append(_make_burn_event(times, d_v, burn_start_idx, n - 2))
# #
# #     burns = [b for b in burns if b.mean_acceleration_m_s2 >= _BURN_THRESHOLD_M_S2]
# #
# #     actual_window = MissionWindow(start=times[0], end=times[-1])
# #     return burns, actual_window
# #
# #
# # def _make_burn_event(times, d_v: np.ndarray, s: int, e: int) -> BurnEvent:
# #     # Solve 59.5·b[k] + 0.5·b[k+1] = d_v[k] backward from the post-burn zero boundary.
# #     # This gives each minute's constant acceleration such that the client's velocity-Verlet
# #     # trapezoid reproduces Horizons truth at every minute boundary, compensating for the
# #     # one-iteration-per-minute averaging between adjacent burn samples.
# #     n_intervals = e - s + 1
# #     b = np.zeros((n_intervals + 1, 3))  # b[n_intervals] stays 0 (post-burn)
# #     for k in range(e, s - 1, -1):
# #         idx = k - s
# #         b[idx] = (d_v[k] - 0.5 * b[idx + 1]) / 59.5
# #
# #     # Ghost pre-minute cancels the 0.5 s of burn that would otherwise bleed into the
# #     # minute before the burn: 59.5·b_ghost + 0.5·b[s] = 0.
# #     b_ghost = -b[0] / 119.0
# #     accelerations_out = np.vstack([b_ghost[np.newaxis, :], b[:-1]])  # (n_intervals + 1, 3)
# #     n_out = n_intervals + 1
# #
# #     start_time = times[s] - timedelta(seconds=_STEP_SECONDS)
# #     end_time = times[s] + timedelta(seconds=n_intervals * _STEP_SECONDS)
# #
# #     # Summary stats computed from the true burn Δv (not the corrected values),
# #     # so burn_vector/mean_acceleration represent the physical burn, not the ghost.
# #     burn_dv_total = float(np.sum(np.linalg.norm(d_v[s:e + 1], axis=1)))
# #     mean_vector = np.mean(d_v[s:e + 1], axis=0) / _STEP_SECONDS
# #     mean_accel = float(np.linalg.norm(mean_vector))
# #
# #     accelerations = [
# #         BurnAcceleration(
# #             datetime=start_time + timedelta(seconds=k * _STEP_SECONDS),
# #             acceleration=accelerations_out[k].tolist(),
# #         )
# #         for k in range(n_out)
# #     ]
# #
# #     return BurnEvent(
# #         start=start_time,
# #         end=end_time,
# #         duration_s=n_out * _STEP_SECONDS,
# #         burn_vector=Vector(x=float(mean_vector[0]), y=float(mean_vector[1]), z=float(mean_vector[2])),
# #         total_delta_v_m_s=burn_dv_total,
# #         mean_acceleration_m_s2=mean_accel,
# #         accelerations=accelerations,
# #     )
#
#
# async def get_trajectory(naif_id: int, window: MissionWindow) -> list[TrajectoryPoint]:
#     """Fetch full trajectory from Horizons at 1-minute resolution. Returns ICRF positions (m) and velocities (m/s)."""
#     return await horizons.get_trajectory_at_time(naif_id, window.start, window.end)
#
#
#
#     # # start = window.start.strftime("%Y-%m-%d %H:%M:%S")
#     # # stop = window.end.strftime("%Y-%m-%d %H:%M:%S")
#     #
#     # # Horizons' vectors() API interprets the epochs start/stop string as TDB.
#     # # Convert the caller's UTC window into TDB calendar representation so that
#     # # Horizons samples at the physical instant the caller asked for.
#     # start = AstroTime(window.start, scale='utc').tdb.strftime("%Y-%m-%d %H:%M:%S")
#     # stop = AstroTime(window.end, scale='utc').tdb.strftime("%Y-%m-%d %H:%M:%S")
#     #
#     #
#     # obj = Horizons(id=str(naif_id), location='@0',
#     #                epochs={'start': start, 'stop': stop, 'step': '1m'})
#     #
#     # vectors = obj.vectors(refplane='frame')
#     #
#     #
#     #
#     # points = []
#     # for row in vectors:
#     #     # Horizons returns JDs in TDB; convert to UTC for consistency with Skyfield
#     #     t = Time(float(row['datetime_jd']), format='jd', scale='tdb').utc.to_datetime(timezone.utc)
#     #     points.append(TrajectoryPoint(
#     #         datetime=t,
#     #         position=[
#     #             float((row['x'] * u.au).to(u.m).value),
#     #             float((row['y'] * u.au).to(u.m).value),
#     #             float((row['z'] * u.au).to(u.m).value),
#     #         ],
#     #         velocity=[
#     #             float((row['vx'] * u.au / u.day).to(u.m / u.s).value),
#     #             float((row['vy'] * u.au / u.day).to(u.m / u.s).value),
#     #             float((row['vz'] * u.au / u.day).to(u.m / u.s).value),
#     #         ],
#     #     ))
#     # return points
