#!/usr/bin/env python3
"""Differential proof using real Python entities and the Godot LocalMatch updater."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from compare_classic_replay import ReplayDifference, compare
from export_classic_replay import MachineGunRound, Mirv, Missile, Shell, _Game
from src.fixedstep import FixedStepRunner

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "tests/fixtures/experience_parity/projectiles.json"


class ReplayPlayer:
    def __init__(self):
        self.buttons = []

    def get_command(self, command, _value):
        from src.player import Player

        return (command == Player.CMD_GUNLEFT and "left" in self.buttons) or (
            command == Player.CMD_GUNRIGHT and "right" in self.buttons
        )


def timing_trace(spec: dict) -> dict:
    runner = FixedStepRunner(step=1.0 / 60.0, max_substeps=8)
    frames = []
    for index, delta in enumerate(spec["deltas"]):
        steps = runner.consume(delta)
        frames.append({"frame": index, "steps": steps, "accumulator": runner.get_accumulator()})
    return {"id": spec["id"], "frames": frames}


def python_trace(spec: dict) -> dict:
    from src.landscape import LandChunk, Landscape

    game = _Game()
    if "ground" in spec:
        # Deserialize the same flat layered world into each production terrain.
        terrain = Landscape.__new__(Landscape)
        terrain._num_of_slices = 500
        terrain._landscape_width = 11.0
        terrain._slice_to_world_conversion = 250.0 / 11.0
        terrain._fall_pause = 0.2
        terrain._fall_acceleration = 5.0
        terrain._land_chunks = []
        for _ in range(500):
            chunk = LandChunk()
            chunk.max_height_1 = chunk.max_height_2 = float(spec["ground"])
            chunk.min_height_1 = chunk.min_height_2 = -10.0
            terrain._land_chunks.append([chunk])
        game.landscape = terrain
    initial = spec["initial"]
    x, y = initial["position"]
    vx, vy = initial["velocity"]
    size, damage = initial["blast"], initial["damage"]
    kind = spec["kind"]
    player = ReplayPlayer() if "commands" in spec else None
    if kind == "missile":
        entity = Missile(game, player, x, y, initial["angle"], size, damage)
        entity._fuel = initial.get("fuel", 3.0)
    elif kind == "mirv":
        entity = Mirv(game, None, x, y, vx, vy, 0.0, size, damage)
    elif kind == "machine_gun":
        entity = MachineGunRound(game, None, x, y, vx, vy, 0.0, damage)
    else:
        entity = Shell(game, None, x, y, vx, vy, 0.0, size, damage, kind == "nuke")
    entity.assign_entity_id(1)
    frames = []
    for tick in range(spec["ticks"] + 1):
        game.now = tick * spec["step"]
        if player is not None:
            for command in spec["commands"]:
                if command["tick"] == tick:
                    player.buttons = command["buttons"]
        alive = True if tick == 0 else bool(entity.update(spec["step"]))
        frame = {"tick": tick, "alive": alive, "position": [entity._x, entity._y], "spawned": []}
        if kind == "machine_gun":
            frame.update(back_position=[entity._x_back, entity._y_back], kill_next_frame=entity._kill_next_frame)
        if kind == "missile":
            frame.update(fuel=entity._fuel, angle=entity._angle, angle_change=entity._angle_change)
        frame["explosions"] = [
            {key: event[key] for key in ("position", "size", "damage", "white_out")} for event in game.explosions
        ]
        for child in game.entities:
            if isinstance(child, Shell):
                frame["spawned"].append(
                    {"position": [child._x, child._y], "velocity": [child._x_launch_vel, child._y_launch_vel]}
                )
        frames.append(frame)
        if not alive:
            break
    return {"id": spec["id"], "frames": frames}


def compare_runs(expected: dict, actual: dict) -> list[dict]:
    # Validate the envelope first: missing/extra/reordered cases cannot disappear
    # because a comparison only iterated over the expected list.
    def identity(run):
        return {
            "schema": run["schema"],
            **{group: [item["id"] for item in run[group]] for group in ("scenarios", "timing")},
        }

    try:
        if expected.keys() != actual.keys():
            raise ReplayDifference("$: replay fields differ")
        compare(identity(expected), identity(actual))
    except (ReplayDifference, KeyError, TypeError) as exc:
        return [{"id": "replay-schema", "status": "failed", "first_difference": str(exc)}]
    results = []
    for group in ("scenarios", "timing"):
        for scenario, candidate in zip(expected[group], actual[group]):
            try:
                # Vector2 is float32: near the +/-100 world-unit boundary,
                # one pixel ULP / 104 is below 1e-5 world units. Only
                # coordinates get that bound; events and ticks stay exact.
                compare(scenario, candidate, field_tolerances={"position": 1.5e-5, "back_position": 1.5e-5})
                outcome = {"id": scenario["id"], "status": "passed"}
            except ReplayDifference as exc:
                outcome = {"id": scenario["id"], "status": "failed", "first_difference": str(exc)}
            results.append(outcome)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    specs = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    expected = {
        "schema": 1,
        "scenarios": [python_trace(spec) for spec in specs["scenarios"]],
        "timing": [timing_trace(spec) for spec in specs["timing"]],
    }
    (args.output / "python.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    target = args.output.resolve() / "godot.json"
    result = subprocess.run(
        [
            str(args.godot_bin.resolve()),
            "--headless",
            "--path",
            str(ROOT / "versao-godot/godot"),
            "--script",
            "res://tests/classic_replay_export.gd",
            "--",
            str(SCENARIOS),
            str(target),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
        env=os.environ.copy(),
    )
    log = result.stdout + result.stderr
    (args.output / "godot.log").write_text(log, encoding="utf-8")
    if result.returncode or "ERROR:" in log:
        print(log)
        return 1
    actual = json.loads(target.read_text(encoding="utf-8"))
    results = compare_runs(expected, actual)
    for outcome in results:
        print(f"{outcome['id']}: {outcome['status']} {outcome.get('first_difference', '')}")
    (args.output / "comparison.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return int(any(item["status"] == "failed" for item in results))


if __name__ == "__main__":
    raise SystemExit(main())
