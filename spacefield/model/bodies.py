from datetime import datetime
from typing import Optional

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


class Axis(BaseModel):
    """
    TODO: consider using a quaternion
    """
    # Represents the time of day
    rotation: Optional[float] = None
    # ICRS vector of the axis, body spins around this axis
    direction: Optional[Vector] = None

class BarycentricEntry(BaseModel):
    name: str
    axis: Optional[Axis] = None
    position: Vector
    velocity: Vector
    # https://docs.pydantic.dev/2.0/usage/types/datetime/
    # YYYY-MM-DD[T]HH:MM[:SS[.ffffff]][Z or [±]HH[:]MM]
    datetime: datetime


