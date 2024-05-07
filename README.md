The initial version of Spacefield offers a concise set of [CORS-friendly HTTP endpoints](https://vortical.hopto.org/spacefield/docs) for accessing 
ephemeris and orientation/frame data of celestial bodies within the solar system. Measurements adhere
to the International Celestial Reference Frame (ICRF), with all distance units standardized in meters.

Currently utilized by [Orri](https://vortical.hopto.org/orri/?state={%20%22target%22:%22Jupiter%22}), which necessitates precise positions, velocities, and orientations of 
celestial bodies.

While recognizing the prevalence of widely-used standards in various tools, this API maintains a
pragmatic, straightforward approach tailored to Orri's evolving needs. Something not found in any of
the other tools/API.

Key components of the underlying stack include:

- Python
- FastAPI for web framework, featuring Pydantic data models and Swagger documentation.
- Uvicorn as the ASGI web server.
- Docker for containerization

The key apis and documentation I used in realizing the API are:
- [Skyfield](https://rhodesmill.org/skyfield/) for computing positions and velocities of the celestial bodies
- https://astropedia.astrogeology.usgs.gov/download/Docs/WGCCRE/WGCCRE2009reprint.pdf for calculating the orientation of bodies. 

### Future direction of this API

The primary focus of this API is currently to serve [Orri](https://vortical.hopto.org/orri/?state={%20%22target%22:%22Uranus%22})'s needs. As Orri's requirements and feature set expand, we anticipate corresponding enhancements to this API. Shortly, expect:

- Inclusion of additional celestial bodies, including satellites with orbits represented as Two Line Elements (TLE).
- Implementation of functionality to register imagery and 3D models linked to bodies/satellites, possibly incorporating multi-tenancy features.

Further developments beyond these are uncertain at this stage. Should this API continue to be active..


### Quick overview of Usage
Although a Swagger endpoint is provided, this section will add a bit of context.


The Endpoints currently serves up data for a small subset of bodies (about 100), representing the planets and the major moons. To get a list 
of supported bodies:

```commandline
curl -X 'GET' \
  'https://vortical.hopto.org/ephemeris/barycentrics/names' \
  -H 'accept: application/json'
```

To get the ephemeris and orientation data for the moon at a specific time ()
```commandline
curl -X 'GET' \
  'https://vortical.hopto.org/ephemeris/barycentrics/moon?time=2024-05-07T17%3A18%3A00.000Z' \
  -H 'accept: application/json'
```
Which will respond with:
```json
{
  "name": "moon",
  "ephemeris": {
    "position": {
      "x": -103213151812.94234,
      "y": -102105449519.62408,
      "z": -44211648225.45397
    },
    "velocity": {
      "x": 20731.46800642197,
      "y": -17939.504725232804,
      "z": -7681.308344513707
    }
  },
  "axis": {
    "rotation": 218.61082467203437,
    "direction": {
      "x": -0.005999879964571669,
      "y": -0.3737000559483818,
      "z": 0.9275301987669118
    },
    "x": [
      -0.781388526480469,
      -0.5770624662413564,
      -0.2375518485302201
    ],
    "y": [
      -0.6240160031001544,
      0.726186737857157,
      0.288542630533667
    ],
    "z": [
      -0.005999879964571669,
      -0.3737000559483818,
      0.9275301987669118
    ]
  },
  "datetime": "2024-05-07T17:18:00Z"
}
```

#### Ephemeris property
All responses will include the `ephemeris` property. In this case, the moon's location from the `solar system barycenter (SSB)`  at time `2024-05-07T17:18:00Z` is:

```json
{
  "position": {
    "x": -103213151812.94234,
    "y": -102105449519.62408,
    "z": -44211648225.45397
  }
}
```

Contrast this position with that of earth's:
```json
{
  "position": {
    "x": -103486241984.77074,
    "y": -102322020430.89778,
    "z": -44321758071.95965
  }
}
```

And the Moon-Earth distance at that time is:

$` sqrt{ (-103213151 - -10348624)^2  + (-102105449 - -102322020)^2 +  (-44211648 - -44321758) ^2 } == 365521`$
So in km is: `~365,521km`

#### Orientation
The orientation is provided by the `axis` property.
```json
"axis": {
    "rotation": 218.61082467203437,
    "direction": {
      "x": -0.005999879964571669,
      "y": -0.3737000559483818,
      "z": 0.9275301987669118
    },
    "x": [
      -0.781388526480469,
      -0.5770624662413564,
      -0.2375518485302201
    ],
    "y": [
      -0.6240160031001544,
      0.726186737857157,
      0.288542630533667
    ],
    "z": [
      -0.005999879964571669,
      -0.3737000559483818,
      0.9275301987669118
    ]
  }
```
If the `axis` property is provided, then `z` axis will always be provided (`direction` is just its alias and will probably be removed).
`z` represents the body's pole/spin axis.

The `rotation` along with associated `x` and `y` properties are currently optional. These properties specify the sidereal rotation; the longitude facing the sun at
a specific time.



## Installation Notes

### Download ephemeris files before starting up

- [de440s.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp)
- [mar097.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/mar097.bsp)
- [jup365.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/jup365.bsp)
- [sat441.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/sat441.bsp)
- [nep095.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/nep095.bsp)
- [ura111.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/ura111.bsp)
- [ura115.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/satellites/ura115.bsp)
- [plu043.bsp](https://naif.jpl.nasa.gov/pub/naif/pds/wgc/kernels/spk/plu043.bsp)

Put them wherever you set the  /spacefield/data volume in docker:
[compose.yaml](compose.yaml)



### Build and run from docker
[README.Docker.md](README.Docker.md)


### Run outside of docker

This section provides instructions for setting up and running the project from the command line or your IDE.


[main.py](./spacefield/main.py)  will start its own Uvicorn server on port 8001 when invoked as the main script.



#### Setup and Execution

##### Using python -m venv:
First, install build dependencies:

```commandline
sudo apt update; sudo apt install build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev curl \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

Next, install pyenv:
```commandline
curl https://pyenv.run | bash
```

Install python version:
```commandline
pyenv install 3.10.13
```


rom the project folder, set up a Python virtual environment using `python -m venv`:
```commandline
pyenv local 3.10.13
python -m venv .venv
source .venv/bin/activate
```

Alternatively, if you prefer using `penv-virtualenv`:

```commandline
pyenv local 3.10.13
pyenv virtualenv 3.10.13 .venv
...
```

Install required packages:
```commandline
pip install -r requirements.txt
```

To run the program as a module:
```commandline
python -m spacefield.main
```

Or, from your IDE, set 'spacefield' as the source root and run main.py.





