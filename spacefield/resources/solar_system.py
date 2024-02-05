from fastapi import APIRouter, HTTPException

from spacefield.model.bodies import Body


router = APIRouter(
    prefix="/solarsystem",
)

names = ["sun", "mercury"]

@router.get("/bodies")
async def get_bodies() -> list[Body]:
    return [Body(name="sun"), Body(name="mercury")]


@router.get("/bodies/names")
async def get_body_names() -> list[str]:
    return names

@router.get("/bodies/{body_name}")
async def get_body(body_name: str) -> Body:
    if body_name not in names:
        raise HTTPException(status_code=404, detail="Item not found")
    return Body(name=body_name)
