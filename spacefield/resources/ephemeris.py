from datetime import datetime, timezone
from fastapi import APIRouter,  HTTPException

from spacefield.model.bodies import BarycentricState, Vector
from spacefield.business import ephemeris

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

