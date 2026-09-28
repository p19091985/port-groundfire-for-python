#!/usr/bin/env python3
"""Export deterministic contracts from the Python classic implementation."""

from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import random
import sys
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "versao-python"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "classic_runtime_reference.json"
GODOT_FIXTURE_PATH = ROOT / "versao-godot" / "godot" / "data" / "classic_runtime_reference.json"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from src.fixedstep import FixedStepRunner  # noqa: E402
from src.gamesimulation import GameSimulationController  # noqa: E402


class _Interface:
    def get_key(self, _key):
        return False


class _Landscape:
    def __init__(self, trace):
        self.trace = trace

    def update(self, dt):
        self.trace.append(["landscape", dt])


class _Entity:
    def __init__(self, name, trace):
        self.name = name
        self.trace = trace

    def update(self, dt):
        self.trace.append([self.name, dt])
        return True


class _Game:
    pygame_module = type("PygameStub", (), {"K_ESCAPE": 27})

    def __init__(self):
        self.trace = []
        self._landscape = _Landscape(self.trace)
        self._entity_list = [_Entity("player_0", self.trace), _Entity("player_1", self.trace)]
        self._new_state = 0

    def get_interface(self):
        return _Interface()

    def remove_entity(self, entity):
        self._entity_list.remove(entity)


def _source_hash(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def _fixed_step_trace(fps: int, frames: int = 24) -> dict:
    runner = FixedStepRunner(step=1.0 / 60.0, max_substeps=8)
    counts = [len(runner.consume(1.0 / fps)) for _ in range(frames)]
    return {"fps": fps, "step_counts": counts, "accumulator": runner.get_accumulator()}


def _controls() -> dict:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(PYTHON_ROOT / "conf" / "controls.ini", encoding="utf-8")
    return {
        section.strip(): {key: int(value) for key, value in parser.items(section)}
        for section in (" Keyboard1 ", " Keyboard2 ", " JoyLayout1 ")
    }


def _options() -> dict:
    parser = configparser.ConfigParser()
    parser.read(PYTHON_ROOT / "conf" / "options.ini", encoding="utf-8")
    return {
        "terrain": {
            "slices": parser.getint("Terrain", "Slices"),
            "width": parser.getfloat("Terrain", "Width"),
            "fall_pause": parser.getfloat("Terrain", "FallPause"),
            "fall_acceleration": parser.getfloat("Terrain", "FallAcceleration"),
        },
        "tank_gravity": parser.getfloat("Tank", "Gravity"),
        "weapon_damage": {
            name.lower(): parser.getfloat(name, "Damage")
            for name in ("Shell", "Nuke", "Missile", "Mirv", "MachineGun")
        },
    }


def _wave_metadata(path: Path) -> dict:
    with wave.open(str(path), "rb") as wav_file:
        frame_count = wav_file.getnframes()
        frame_rate = wav_file.getframerate()
        return {
            "channels": wav_file.getnchannels(),
            "sample_width_bytes": wav_file.getsampwidth(),
            "sample_rate": frame_rate,
            "frames": frame_count,
            "duration_seconds": round(frame_count / frame_rate, 9),
        }


def _asset_manifest() -> list[dict]:
    manifest = json.loads((PYTHON_ROOT / "conf" / "assets.json").read_text(encoding="utf-8"))
    records = []
    for group_name in ("textures", "sounds"):
        for entry in manifest[group_name]:
            relative_source = entry["candidates"][0]
            source = PYTHON_ROOT / relative_source
            target = ROOT / "versao-godot" / "godot" / "assets" / source.name
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            target_hash = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
            record = {
                "id": int(entry["id"]),
                "key": str(entry["key"]),
                "kind": group_name[:-1],
                "filename": source.name,
                "python_sha256": source_hash,
                "godot_sha256": target_hash,
                "transfer": "preserved" if source_hash == target_hash else "converted",
                "usage": "declared_reference_unused" if entry["key"] == "damage" else "runtime",
            }
            if group_name == "sounds":
                record["python_audio"] = _wave_metadata(source)
                record["godot_audio"] = _wave_metadata(target)
            records.append(record)
    return records


def _terrain_heights(seed: int, slices: int = 500) -> list[float]:
    rng = random.Random(seed)
    heights = [-7.0] * (slices + 1)
    smoothed = [0.0] * (slices + 1)
    for _ in range(18):
        centre = rng.randrange((slices + 1) * 2) - ((slices + 1) // 2)
        mound_height = rng.randrange(1000) / 300.0
        mound_width = rng.randrange((slices + 1) // 2) + 3
        plateau = rng.randrange(max(1, mound_width // 3))
        for index in range(slices + 1):
            distance = abs(centre - index)
            if distance < plateau:
                heights[index] += mound_height
            elif distance < mound_width:
                heights[index] += ((mound_width - (distance - plateau)) / mound_width) * mound_height
            heights[index] = min(5.0, heights[index])
    for index in range(slices + 1):
        if 10 <= index < slices - 10:
            smoothed[index] = sum(heights[index - 10 : index + 11]) / 21.0
        else:
            smoothed[index] = heights[index]
    return [round(value, 7) for value in smoothed]


def build_fixture() -> dict:
    game = _Game()
    GameSimulationController().update_round(game, 1.0 / 60.0)
    slow = FixedStepRunner(step=1.0 / 60.0, max_substeps=8)
    slow_steps = slow.consume(0.5)
    return {
        "schema": 1,
        "reference": "versao-python classic runtime",
        "sources": {
            path: _source_hash(path)
            for path in (
                "versao-python/src/fixedstep.py",
                "versao-python/src/gamesimulation.py",
                "versao-python/src/shopmenu.py",
                "versao-python/conf/controls.ini",
                "versao-python/conf/options.ini",
            )
        },
        "fixed_step": {
            "step": 1.0 / 60.0,
            "max_substeps": 8,
            "frame_traces": [_fixed_step_trace(fps) for fps in (30, 60, 144)],
            "slow_frame": {"input_delta": 0.5, "step_count": len(slow_steps), "accumulator": slow.get_accumulator()},
        },
        "simultaneous_round": {"update_trace": game.trace, "entity_count": len(game._entity_list)},
        "shop": {
            "slots": 8,
            "initial_positions": [0] * 8,
            "initial_delays": [0.4] * 8,
            "initial_done": [False] * 8,
            "action_delay": 0.2,
            "done_position": 10,
        },
        "terrain_rng": {
            "seed": 1401,
            "randrange_stops": [1002, 1000, 250, 20, 1002, 1000, 250, 30],
            "values": [749, 908, 113, 1, 736, 163, 127, 13],
            "world_heights": _terrain_heights(1401),
        },
        "controls": _controls(),
        "options": _options(),
        "assets": _asset_manifest(),
        "online_slot_2": {
            "local_player_number": 2,
            "entities": [
                {"entity_id": 41, "entity_type": "tank", "owner_player": 1},
                {"entity_id": 42, "entity_type": "tank", "owner_player": 2},
                {"entity_id": 43, "entity_type": "shell", "owner_player": 2},
            ],
            "predicted_entity_ids": [42],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build_fixture(), indent=2, sort_keys=True) + "\n"
    if args.check:
        for fixture_path in (FIXTURE_PATH, GODOT_FIXTURE_PATH):
            if not fixture_path.exists() or fixture_path.read_text(encoding="utf-8") != rendered:
                print(f"Classic reference fixture is stale: {fixture_path}", file=sys.stderr)
                return 1
        print("Classic reference fixture is current.")
        return 0
    if args.write:
        for fixture_path in (FIXTURE_PATH, GODOT_FIXTURE_PATH):
            fixture_path.parent.mkdir(parents=True, exist_ok=True)
            fixture_path.write_text(rendered, encoding="utf-8")
        print(FIXTURE_PATH)
        return 0
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
