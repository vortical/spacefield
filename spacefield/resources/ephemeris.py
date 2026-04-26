
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from spacefield.model.bodies import BarycentricState, SpacecraftInfo, BurnEvent, TrajectoryPoint
from spacefield.business import ephemeris
from spacefield.business.spacecraft import get_ephemeris, get_spacecrafts, get_spacecraft, get_burns, get_trajectory



router = APIRouter(
    prefix="/ephemeris",
)


@router.get("/bodies")
async def get_body_names() -> list[str]:
    return ephemeris.get_names()


@router.get("/bodies/{entry_name}")
async def get_body(entry_name, time: datetime) -> BarycentricState:
    state = ephemeris.get_state(entry_name, time)
    if not state:
        raise HTTPException(status_code=404, detail="Item not found")
    return state


@router.get("/spacecraft")
async def list_spacecraft() -> list[SpacecraftInfo]:
    return list(get_spacecrafts().values())


@router.get("/spacecraft/{name}")
async def get_spacecraft_state(name: str, time: datetime) -> BarycentricState:
    spacecraft = get_spacecraft(name)
    if spacecraft is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")

    try:
        return await get_ephemeris(spacecraft, time)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"JPL Horizons error: {e}")

@router.get("/spacecraft/{name}/burns")
async def get_spacecraft_burns(name: str) -> list[BurnEvent]:
    spacecraft = get_spacecraft(name)
    if spacecraft is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    return await get_burns(spacecraft)


@router.get("/spacecraft/{name}/trajectory")
async def get_spacecraft_trajectory(name: str, step: int = 1) -> list[TrajectoryPoint]:
    spacecraft = get_spacecraft(name)
    if spacecraft is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    if spacecraft.mission_window is None:
        raise HTTPException(status_code=400, detail=f"No mission_window defined for '{name}' in the registry")
    try:
        return await get_trajectory( spacecraft, step)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Trajectory error: {e}")

