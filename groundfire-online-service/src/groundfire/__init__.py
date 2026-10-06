from __future__ import annotations

from importlib import import_module

__all__ = [
    "ClientApp",
    "EntityRegistry",
    "MatchSnapshot",
    "MatchState",
    "ReplicatedEntityState",
    "ReplicatedPlayerState",
    "ServerApp",
    "TerrainPatch",
    "TerrainState",
    "WorldState",
]


def __getattr__(name: str):
    if name in {"ClientApp", "ServerApp"}:
        return getattr(import_module("src.groundfire.app"), name)
    if name in {"EntityRegistry", "ReplicatedEntityState", "TerrainPatch", "TerrainState", "WorldState"}:
        return getattr(import_module("src.groundfire.sim"), name)
    if name in {"MatchSnapshot", "MatchState", "ReplicatedPlayerState"}:
        return getattr(import_module("src.groundfire.sim"), name)
    raise AttributeError(name)
