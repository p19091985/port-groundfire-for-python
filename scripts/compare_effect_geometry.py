"""Compare evolving smoke geometry against real Python Smoke render primitives."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot-bin", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "versao-python"))
    from src.smoke import Smoke

    cases = []
    for texture, rotation_rate, growth_rate, fade_rate in ((0, 0.1, 0.3, 0.1), (1, 0.0, 0.6, 0.8)):
        smoke = Smoke(None, 2.0, 1.0, 0.2, 0.5, texture, rotation_rate, growth_rate, fade_rate)
        frames = []
        for tick in range(601):
            alive = smoke.update(1 / 60) if tick else True
            primitive = smoke.get_render_state().primitives[0]
            frames.append(
                {
                    "tick": tick,
                    "alive": alive,
                    "width": primitive.width,
                    "rotation": primitive.rotation,
                    "position": [primitive.x, primitive.y],
                }
            )
            if not alive:
                break
        cases.append(
            {
                "texture": texture,
                "rotation_rate": rotation_rate,
                "growth_rate": growth_rate,
                "fade_rate": fade_rate,
                "frames": frames,
            }
        )
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    reference = output / "python-smoke.json"
    reference.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    env = dict(os.environ, EXPERIENCE_SMOKE_REFERENCE=str(reference))
    result = subprocess.run(
        [
            str(args.godot_bin.resolve()),
            "--headless",
            "--path",
            str(ROOT / "versao-godot/godot"),
            "--script",
            "res://tests/effect_geometry_check.gd",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    log = result.stdout + result.stderr
    (output / "godot.log").write_text(log, encoding="utf-8")
    print(log, end="")
    passed = result.returncode == 0 and "ERROR:" not in log and "Smoke geometry comparison passed" in log
    (output / "report.json").write_text(
        json.dumps(
            {"passed": passed, "cases": len(cases), "frames": sum(len(case["frames"]) for case in cases)}, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
