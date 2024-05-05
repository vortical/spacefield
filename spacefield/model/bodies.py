from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

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

