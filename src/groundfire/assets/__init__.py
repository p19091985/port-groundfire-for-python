from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

__all__ = [
    "DEFAULT_MANIFEST_PATH",
    "AssetSpec",
    "find_spec_by_key",
    "load_sound_specs",
    "load_texture_specs",
    "resolve_asset_path",
]

DEFAULT_MANIFEST_PATH = Path("conf/assets.json")


@dataclass(frozen=True)
class AssetSpec:
    asset_id: int
    key: str
    candidates: tuple[str, ...]


def _read_manifest(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> dict:
    path = Path(manifest_path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_specs(entries: Iterable[dict]) -> list[AssetSpec]:
    return [
        AssetSpec(
            asset_id=int(entry["id"]),
            key=str(entry["key"]),
            candidates=tuple(str(candidate) for candidate in entry["candidates"]),
        )
        for entry in entries
    ]


def load_texture_specs(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> list[AssetSpec]:
    return _parse_specs(_read_manifest(manifest_path).get("textures", []))


def load_sound_specs(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> list[AssetSpec]:
    return _parse_specs(_read_manifest(manifest_path).get("sounds", []))


def find_spec_by_key(specs: Iterable[AssetSpec], key: str) -> AssetSpec | None:
    for spec in specs:
        if spec.key == key:
            return spec
    return None


def resolve_asset_path(candidates: Iterable[str], *, root: str | Path = ".") -> Path | None:
    root_path = Path(root)
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = root_path / path
        if path.exists():
            return path
    return None
