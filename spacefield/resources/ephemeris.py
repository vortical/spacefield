from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from spacefield.model.bodies import BarycentricState
from spacefield.business import ephemeris
from spacefield.kernels.horizons import get_horizons_state

router = APIRouter(
    prefix="/ephemeris",
)

@router.get("/barycentrics/names")
async def get_barycentric_entry_names() -> list[str]:
    return ephemeris.get_names()


@router.get("/barycentrics/{entry_name}")
async def get_barycentric_entry(entry_name, time: datetime) -> BarycentricState:
    state = ephemeris.get_state(entry_name, time)
    if not state:
        raise HTTPException(status_code=404, detail="Item not found")
    return state




@router.get("/spacecraft/artemis2")
async def get_artemis2(time: datetime) -> BarycentricState:
    try:
        eph = await get_horizons_state(-1024, time)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"JPL Horizons error: {e}")
    return BarycentricState(
        name="artemis2",
        ephemeris=eph,
        axis=None,
        datetime=time.astimezone(timezone.utc),
    )

