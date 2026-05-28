# spacefield

A FastAPI service that serves solar-system ephemeris and body-orientation data over HTTP.

Positions and velocities are returned in the International Celestial Reference Frame (ICRF), in **meters** and **meters per second**, relative to the Solar System Barycenter. Orientation is returned as a body-fixed frame plus a sidereal rotation angle.

Serves [**Orri**](https://vortical.hopto.org/orri/), a 3D solar-system visualizer.

- Swagger: [`vortical.hopto.org/spacefield/docs`](https://vortical.hopto.org/spacefield/docs)

## API

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/ephemeris/bodies` | List of available bodies (Sun, planets, major moons, Pluto system). |
| `GET` | `/ephemeris/bodies/{name}?time={ISO8601}` | Position, velocity, and orientation of a body at a given UTC time. |
| `GET` | `/ephemeris/spacecraft` | Registered spacecraft (currently Artemis I, Artemis II, Perseverance). |
| `GET` | `/ephemeris/spacecraft/{name}?time={ISO8601}` | Spacecraft state at a given UTC time. Backed by JPL Horizons. |
| `GET` | `/ephemeris/spacecraft/{name}/burns` | Detected burn events along the spacecraft's trajectory. |
| `GET` | `/ephemeris/spacecraft/{name}/trajectory?step={int}` | Trajectory samples across the mission window. |
| `GET` | `/ephemeris/spacecraft/{name}/missionwindow` | Time range for which Horizons has data for the spacecraft. |

## Example

```bash
curl 'https://vortical.hopto.org/spacefield/ephemeris/bodies/moon?time=2024-05-07T17:18:00Z'
```

```json
{
  "name": "moon",
  "ephemeris": {
    "position": { "x": -103213151812.94, "y": -102105449519.62, "z":  -44211648225.45 },
    "velocity": { "x":      20731.4680,   "y":     -17939.5047,   "z":      -7681.3083 }
  },
  "axis": {
    "rotation": 218.61082467203437,
    "direction": { "x": -0.0060, "y": -0.3737, "z":  0.9275 },
    "x": [-0.7814, -0.5771, -0.2376],
    "y": [-0.6240,  0.7262,  0.2885],
    "z": [-0.0060, -0.3737,  0.9275]
  },
  "datetime": "2024-05-07T17:18:00Z"
}
```

`ephemeris.position` and `ephemeris.velocity` are barycentric ICRF vectors in meters and m·s⁻¹. `axis.z` is the body's spin pole; `axis.x`/`axis.y` plus `axis.rotation` give the prime-meridian frame at the requested time.

## Quickstart

```bash
# List bodies
curl 'https://vortical.hopto.org/spacefield/ephemeris/bodies'

# Get a body's state at a UTC time
curl 'https://vortical.hopto.org/spacefield/ephemeris/bodies/mars?time=2026-04-02T00:00:00Z'

# Get a spacecraft's state (queries JPL Horizons)
curl 'https://vortical.hopto.org/spacefield/ephemeris/spacecraft/artemis2?time=2026-04-02T01:57:24Z'
```

## Technical highlights

- **ICRF barycentric coordinates throughout.** Position and velocity are SI units against the solar-system barycenter — usable directly in physics computations, no frame transforms required at the caller.
- **Dual orientation pipeline.** SPICE BPC/TF/TPC kernels drive the Moon (MOON_ME_DE421 frame); IAU WGCCRE 2009 analytic pole and prime-meridian models cover the Sun, planets, and major satellites.
- **JPL Horizons integration for spacecraft.** Spacecraft ephemerides (Artemis I/II, Perseverance) are queried from NASA's Horizons system via `astroquery`, with TDB ↔ UTC conversion handled correctly (~69 s offset, ~2000 km positional impact if ignored).
- **Spacecraft burn detection.** Spacecraft trajectory points are differentiated against the local gravity field to surface burn events as discrete `BurnEvent` records.
- **Async FastAPI + Pydantic.** Strict response models for every endpoint. Blocking Skyfield and astroquery calls are offloaded via `asyncio.to_thread` so the event loop stays responsive.

## Running the service

### Docker (recommended)

```bash
docker compose up --build
```

The API and Swagger UI are then at `http://localhost:8000/docs`.

### Outside Docker

```bash
pyenv install 3.11.6
pyenv local 3.11.6
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacefield.main
```

Defaults to port 8001 when run as a module.

## Required data files

The service expects the following files in the directory pointed to by `DATA_PATH` (default `/spacefield/data` inside the container).

**SPK ephemeris kernels** (position and velocity):

- `de440s.bsp`, `mar097.bsp`, `jup365.bsp`, `sat441.bsp`, `nep095.bsp`, `ura111.bsp`, `ura115.bsp`, `plu043.bsp`

**SPICE orientation kernels** (Moon):

- `moon_080317.tf`, `pck00008.tpc`, `moon_pa_de421_1900-2050.bpc`

**Other:**

- `gm_de440.tpc` — gravitational parameters used by burn detection
- `spacecraft_registry.json` — spacecraft NAIF IDs and metadata for the `/spacecraft` endpoints

Coverage of the supplied kernels: **1 Jan 1995 — 31 Dec 2050**.

Most SPK kernels are mirrored at the NAIF [generic kernels](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/) repository.

## References

- [Skyfield](https://rhodesmill.org/skyfield/) — ephemeris loading and time scales
- [WGCCRE 2009 Report on Cartographic Coordinates and Rotational Elements](https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/atoms/files/WGCCRE2009reprint.pdf) — IAU body orientation models
- [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) — spacecraft ephemerides
