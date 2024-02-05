from datetime import datetime, timezone

from fastapi import APIRouter
import pytz

from spacefield.model.bodies import BarycentricEntry, Vector
from spacefield.business import ephemeris

router = APIRouter(
    prefix="/ephemerids",
)

@router.get("/barycentrics/names")
async def get_barycentric_entry_names() -> list[str]:
    return ephemeris.get_names()


@router.get("/barycentrics/{entry_name}")
async def get_barycentric_entry(entry_name, time: datetime) -> BarycentricEntry:
    return ephemeris.position(entry_name, time)
    # return BarycentricEntry(name=entry_name, position=Vector(x=0, y=0, z=0), velocity=Vector(x=0, y=0,z=0), datetime=now_utc.astimezone(pacific_timezone))

    #

