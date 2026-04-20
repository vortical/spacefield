
import json
import os
from typing import Optional

from spacefield.config import SPACECRAFT_REGISTRY_PATH, BURNS_DIRECTORY, TRAJECTORY_DIRECTORY
from spacefield.model.bodies import SpacecraftInfo, BurnEvent, MissionWindow, TrajectoryPoint
from spacefield.kernels.trajectory import fetch_trajectory


def _load_registry() -> list[dict]:
    with open(SPACECRAFT_REGISTRY_PATH) as f:
        return json.load(f)


def get_spacecraft_list() -> list[SpacecraftInfo]:
    return [SpacecraftInfo(**entry) for entry in _load_registry()]


def get_spacecraft(name: str) -> Optional[SpacecraftInfo]:
    for entry in _load_registry():
        if entry["name"].lower() == name.lower():
            return SpacecraftInfo(**entry)
    return None


def get_naif_id(name: str) -> Optional[int]:
    sc = get_spacecraft(name)
    return sc.naif_id if sc else None


def _burns_path(name: str) -> str:
    return os.path.join(BURNS_DIRECTORY, f"{name}.json")


def load_burns(name: str) -> list[BurnEvent]:
    path = _burns_path(name)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    # Support both new format {"mission_window": ..., "burns": [...]} and legacy list
    burns_data = data.get("burns", data) if isinstance(data, dict) else data
    return [BurnEvent(**b) for b in burns_data]


def load_mission_window(name: str) -> Optional[MissionWindow]:
    path = _burns_path(name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict) and "mission_window" in data:
        return MissionWindow(**data["mission_window"])
    return None


def save_burns(name: str, burns: list[BurnEvent], window: MissionWindow) -> None:
    os.makedirs(BURNS_DIRECTORY, exist_ok=True)
    with open(_burns_path(name), "w") as f:
        json.dump({
            "mission_window": window.model_dump(mode="json"),
            "burns": [b.model_dump(mode="json") for b in burns],
        }, f, indent=2)


def _trajectory_path(name: str) -> str:
    return os.path.join(TRAJECTORY_DIRECTORY, f"{name}.json")


def save_trajectory(name: str, points: list[TrajectoryPoint]) -> None:
    os.makedirs(TRAJECTORY_DIRECTORY, exist_ok=True)
    with open(_trajectory_path(name), "w") as f:
        json.dump([p.model_dump(mode="json") for p in points], f)


def get_trajectory(sc: SpacecraftInfo, step: int = 1, force_refresh: bool = False) -> list[TrajectoryPoint]:
    path = _trajectory_path(sc.name)
    if not force_refresh and os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        return [TrajectoryPoint(**p) for p in data[::step]]
    points = fetch_trajectory(sc.naif_id, sc.mission_window)
    save_trajectory(sc.name, points)
    return points[::step]
