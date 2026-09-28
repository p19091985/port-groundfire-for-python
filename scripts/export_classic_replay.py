#!/usr/bin/env python3
"""Export deterministic traces by running the real classic projectile classes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "versao-python"
DEFAULT_OUTPUT = ROOT / "tests" / "fixtures" / "classic_replays" / "python_projectiles.json"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from src.machinegunround import MachineGunRound  # noqa: E402
from src.mirv import Mirv  # noqa: E402
from src.missile import Missile  # noqa: E402
from src.shell import Shell  # noqa: E402


class _Landscape:
    @staticmethod
    def get_landscape_width() -> float:
        return 100.0

    @staticmethod
    def ground_collision(_old_x: float, _old_y: float, _x: float, _y: float) -> tuple[bool, float, float]:
        return False, 0.0, 0.0


class _Game:
    def __init__(self):
        self.now = 0.0
        self.entities: list[object] = []
        self.explosions: list[dict] = []
        self.landscape = _Landscape()

    def get_time(self) -> float:
        return self.now

    def add_entity(self, entity: object) -> None:
        self.entities.append(entity)

    def get_landscape(self) -> _Landscape:
        return self.landscape

    @staticmethod
    def get_players() -> list:
        return []

    @staticmethod
    def get_sound():
        return None

    def explosion(self, x, y, size, damage, hit_tank, sound_id, white_out, _player) -> None:
        self.explosions.append(
            {
                "position": [_number(x), _number(y)],
                "size": _number(size),
                "damage": _number(damage),
                "hit_tank": hit_tank,
                "sound_id": sound_id,
                "white_out": bool(white_out),
            }
        )


def _number(value: float) -> float:
    return round(float(value), 9)


def _state(entity: object, tick: int, alive: bool, game: _Game) -> dict:
    record = {
        "tick": tick,
        "time": _number(game.now),
        "alive": alive,
        "position": [_number(getattr(entity, "_x")), _number(getattr(entity, "_y"))],
    }
    for name in ("_x_back", "_y_back", "_fuel", "_angle", "_angle_change", "_kill_next_frame"):
        if hasattr(entity, name):
            value = getattr(entity, name)
            record[name.removeprefix("_")] = bool(value) if isinstance(value, bool) else _number(value)
    spawned = []
    for child in game.entities:
        if child is entity or child.__class__.__name__ == "Trail":
            continue
        spawned.append(
            {
                "type": child.__class__.__name__.lower(),
                "position": [_number(getattr(child, "_x", 0.0)), _number(getattr(child, "_y", 0.0))],
                "velocity": [
                    _number(getattr(child, "_x_launch_vel", 0.0)),
                    _number(getattr(child, "_y_launch_vel", 0.0)),
                ],
            }
        )
    record["spawned"] = spawned
    record["explosions"] = list(game.explosions)
    return record


def _trace(name: str, factory, *, ticks: int = 220, step: float = 1.0 / 60.0) -> dict:
    game = _Game()
    entity = factory(game)
    entity.assign_entity_id(1)
    game.add_entity(entity)
    frames = []
    alive = True
    for tick in range(ticks + 1):
        game.now = tick * step
        if tick:
            alive = bool(entity.update(step))
        frames.append(_state(entity, tick, alive, game))
        if not alive:
            break
    return {"scenario_id": name, "step": step, "frames": frames}


def build_replay() -> dict:
    scenarios = [
        _trace("shell_free_flight", lambda game: Shell(game, None, 1.0, 2.0, 3.0, 4.0, 0.0, 0.6, 40.0, False)),
        _trace("nuke_free_flight", lambda game: Shell(game, None, 1.0, 2.0, 3.0, 4.0, 0.0, 1.2, 100.0, True)),
        _trace("machine_gun_free_flight", lambda game: MachineGunRound(game, None, 1.0, 2.0, 8.0, 3.0, 0.0, 2.0)),
        _trace("mirv_split", lambda game: Mirv(game, None, 1.0, 2.0, 3.0, 4.0, 0.0, 0.5, 30.0)),
        _trace("missile_powered_flight", lambda game: Missile(game, None, 1.0, 2.0, 25.0, 0.5, 40.0)),
    ]
    sources = {}
    for relative in ("shell.py", "machinegunround.py", "mirv.py", "missile.py", "weapons_impl.py"):
        path = PYTHON_ROOT / "src" / relative
        sources[f"versao-python/src/{relative}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": 1,
        "reference": "versao-python classic projectile runtime",
        "units": {"position": "classic_world", "velocity": "classic_world_per_second", "time": "seconds"},
        "sources": sources,
        "scenarios": scenarios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = json.dumps(build_replay(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != generated:
            print(f"Classic replay fixture is stale: {args.output}", file=sys.stderr)
            return 1
        print(f"Classic replay fixture is current: {args.output}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
