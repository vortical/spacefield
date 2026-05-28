import asyncio
import json
import os
import re


from datetime import datetime, timezone, timedelta
from typing import Optional
from functools import cache

from spacefield.config import SPACECRAFT_REGISTRY_PATH, BURNS_DIRECTORY, TRAJECTORY_DIRECTORY
from spacefield.model.bodies import SpacecraftInfo, BurnEvent, MissionWindow, TrajectoryPoint, Ephemeris, \
    BarycentricState
import spacefield.kernels.trajectory as trajectory_service
import spacefield.kernels.burns as burns_service

from astropy.time import Time as AstroTime

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

async def get_mission_window(spacecraft: SpacecraftInfo) -> MissionWindow:

    async def handle_boundary(spacecraft: SpacecraftInfo, time: datetime) -> datetime:

        # Convert Horizons format "2026-APR-02 01:58:32.3050" to ISO before parsing
        def _horizons_date_to_astrotime(horizons_str: str) -> AstroTime:
            # Parse Horizons' non-standard format: YYYY-MON-DD HH:MM:SS.SSSS
            dt = datetime.strptime(horizons_str.strip(), "%Y-%b-%d %H:%M:%S.%f")
            return AstroTime(dt, scale='tdb')

        try:
            ephemeris = await get_ephemeris(spacecraft, time)
            # If no exception, the epoch was valid — shouldn't happen with year 0 / 3000
            raise RuntimeError(f"Expected out-of-bounds error  for  {spacecraft.name} at epoch {time}")
        except RuntimeError:
            raise
        except Exception as e:
            error_msg = str(e)
            match = re.search(r'(?:prior to|after) A\.D\.\s+([\d]{4}-[A-Z]{3}-[\d]{2}\s[\d:\.]+)\s+TD', error_msg)
            if match:
                t = match.group(1)
                return _horizons_date_to_astrotime(t).utc.to_datetime(timezone.utc)

            raise RuntimeError(f"Horizons query failed for  {spacecraft.name}: {error_msg}")

    datetime(1000, 1, 1, tzinfo=timezone.utc)

    start, end = await asyncio.gather(
        handle_boundary(spacecraft, datetime(1000, 1, 1, tzinfo=timezone.utc)),
        handle_boundary(spacecraft, datetime(3000, 1, 1, tzinfo=timezone.utc))
    )

    # Start: round up to next whole second to stay safely inside the valid range
    if start.microsecond > 0:
        start = start.replace(microsecond=0) + timedelta(seconds=1)

    # End: truncate to whole second to stay safely inside the valid range
    end = end.replace(microsecond=0)


    return MissionWindow(start=start, end=end)

