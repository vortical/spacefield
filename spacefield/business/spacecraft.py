import asyncio
import json
import os

from datetime import datetime, timezone
from typing import Optional
from functools import cache

from spacefield.config import SPACECRAFT_REGISTRY_PATH, BURNS_DIRECTORY, TRAJECTORY_DIRECTORY
from spacefield.model.bodies import SpacecraftInfo, BurnEvent, MissionWindow, TrajectoryPoint, Ephemeris, \
    BarycentricState
import spacefield.kernels.trajectory as trajectory_service
import spacefield.kernels.burns as burns_service


import spacefield.kernels.horizons as horizons



@cache
def get_spacecrafts() -> dict[str, SpacecraftInfo]:
    def do_load():
        with open(SPACECRAFT_REGISTRY_PATH) as f:
            return { entry["name"].lower(): SpacecraftInfo(**entry) for entry in json.load(f)}

    return do_load()

def get_spacecraft(name: str) -> Optional[SpacecraftInfo]:
    return get_spacecrafts().get(name.lower())



def _burns_path(name: str) -> str:
    return os.path.join(BURNS_DIRECTORY, f"{name}.json")



async def save_burns_to_file(name: str, burns: list[BurnEvent]) -> None:
    def do_save():
        os.makedirs(BURNS_DIRECTORY, exist_ok=True)
        with open(_burns_path(name), "w") as f:
            json.dump([p.model_dump(mode="json") for p in burns], f)

    return await asyncio.to_thread(do_save)


async def create_burns(spacecraft: SpacecraftInfo) -> list[BurnEvent]:
    trajectory_points = await get_trajectory(spacecraft)
    burns = await burns_service.analyze_trajectory(trajectory_points)
    await save_burns_to_file(spacecraft.name, burns)
    return burns


async def load_burns_from_file(spacecraft: SpacecraftInfo)-> list[BurnEvent]|None:
    def do_load():
        path = _burns_path(spacecraft.name)
        if os.path.exists(path):
            with open(path) as f:
                return [BurnEvent(**p) for p in json.load(f)]

        return None

    return await asyncio.to_thread(do_load)


async def get_burns(spacecraft: SpacecraftInfo) -> list[BurnEvent]:

    burns = await load_burns_from_file(spacecraft)
    if not burns:
        burns = await create_burns(spacecraft)

    return burns


def _trajectory_path(name: str) -> str:
    return os.path.join(TRAJECTORY_DIRECTORY, f"{name}.json")


async def save_trajectory_to_file(name: str, points: list[TrajectoryPoint]) -> None:
    def do_save():
        os.makedirs(TRAJECTORY_DIRECTORY, exist_ok=True)
        with open(_trajectory_path(name), "w") as f:
            json.dump([p.model_dump(mode="json") for p in points], f)
    return await asyncio.to_thread(do_save)

async def load_trajectory_from_file(spacecraft: SpacecraftInfo)-> list[TrajectoryPoint]|None:
    def do_load():
        path = _trajectory_path(spacecraft.name)
        if os.path.exists(path):
            with open(path) as f:
                return [TrajectoryPoint(**p) for p in json.load(f)]

        return None

    return await asyncio.to_thread(do_load)


async def create_trajectory(spacecraft: SpacecraftInfo) -> list[TrajectoryPoint]:
    points = await horizons.get_trajectory_at_time(spacecraft.naif_id, spacecraft.mission_window.start, spacecraft.mission_window.end)

    await save_trajectory_to_file(spacecraft.name, points)
    return points




async def get_trajectory(spacecraft: SpacecraftInfo, step: int = 1) -> list[TrajectoryPoint]:
    points = await load_trajectory_from_file(spacecraft)
    if not points:
        points = await create_trajectory(spacecraft)

    return points[::step]

async def get_ephemeris(spacecraft: SpacecraftInfo,  time: datetime) -> BarycentricState:
    ephemeris = await horizons.get_ephemeris_at_time(spacecraft.naif_id, time)

    return BarycentricState(
        name=spacecraft.name,
        ephemeris=ephemeris,
        axis=None, # direction of travel?
        datetime=time.astimezone(timezone.utc),
    )