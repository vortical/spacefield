import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from spacefield.model.bodies import BarycentricState, SpacecraftInfo, BurnEvent, TrajectoryPoint
from spacefield.business import ephemeris
from spacefield.business.spacecraft import get_spacecraft_list, get_spacecraft, load_burns, load_mission_window, save_burns, get_trajectory
from spacefield.kernels.horizons import get_horizons_state
from spacefield.kernels.trajectory import analyze_trajectory

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
    spacecraft = get_spacecraft_list()
    for sc in spacecraft:
        window = load_mission_window(sc.name)
        if window is not None:
            sc.mission_window = window
    return spacecraft


@router.get("/spacecraft/{name}")
async def get_spacecraft_state(name: str, time: datetime) -> BarycentricState:
    sc = get_spacecraft(name)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    naif_id = sc.naif_id
    try:
        eph = await get_horizons_state(naif_id, time)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"JPL Horizons error: {e}")
    return BarycentricState(
        name=name,
        ephemeris=eph,
        axis=None,
        datetime=time.astimezone(timezone.utc),
    )


@router.get("/spacecraft/{name}/burns")
async def get_burns(name: str) -> list[BurnEvent]:
    if get_spacecraft(name) is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    return load_burns(name)


@router.get("/spacecraft/{name}/trajectory")
async def get_spacecraft_trajectory(name: str, step: int = 1, force_refresh: bool = False) -> list[TrajectoryPoint]:
    sc = get_spacecraft(name)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    if sc.mission_window is None:
        raise HTTPException(status_code=400, detail=f"No mission_window defined for '{name}' in the registry")
    try:
        return await asyncio.to_thread(get_trajectory, sc, step, force_refresh)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Trajectory error: {e}")


@router.post("/spacecraft/{name}/burns/compute")
async def compute_burns(name: str) -> list[BurnEvent]:
    sc = get_spacecraft(name)
    if sc is None:
        raise HTTPException(status_code=404, detail=f"Spacecraft '{name}' not found")
    if sc.mission_window is None:
        raise HTTPException(status_code=400, detail=f"No mission_window defined for '{name}' in the registry")
    try:
        burns, window = await asyncio.to_thread(analyze_trajectory, sc.naif_id, sc.mission_window)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Trajectory analysis error: {e}")
    save_burns(name, burns, window)
    return burns
