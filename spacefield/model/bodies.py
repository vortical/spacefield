from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from pydantic.alias_generators import to_camel

class Body(BaseModel):
    name: str
    description: str | None = None

class Vector(BaseModel):
    x: float
    y: float
    z: float

    @classmethod
    def from_array(cls, nparray) -> 'cls':
        return cls(x=nparray[0], y=nparray[1], z=nparray[2])


class Polar(BaseModel):
    ra: float
    dec: float
    # Prime Meridian
    pm: float


class Ephemeris(BaseModel):
    position: Vector
    velocity: Vector


class Axis(BaseModel):
    # Represents the time of day
    rotation: Optional[float] = None
    # ICRS vector of the axis, body spins around this axis
    direction: Optional[Vector] = None
    # Alternative representation for Axis: just use polar

    x: Optional[List[float]] = None
    y: Optional[List[float]] = None

    # todo: this is same a direction
    z: Optional[List[float]] = None

class BarycentricState(BaseModel):
    name: str
    ephemeris: Ephemeris
    axis: Optional[Axis] = None
    # https://docs.pydantic.dev/2.0/usage/types/datetime/
    # YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]
    datetime: datetime


class MissionWindow(BaseModel):
    start: datetime
    end: datetime


class SpacecraftInfo(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    name: str
    naif_id: int
    description: str
    mission_window: Optional[MissionWindow] = None


class TrajectoryPoint(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    datetime: datetime
    ephemeris: Ephemeris


class BurnEvent(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)
    start: datetime
    end: datetime
    duration_s: float
    burn_vector: Vector           # mean non-gravitational acceleration, m/s², ICRF
    total_delta_v_m_s: float      # m/s, integrated residual acceleration × step
    mean_acceleration_m_s2: float

