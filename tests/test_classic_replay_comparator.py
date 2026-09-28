from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_classic_replay import ReplayDifference, compare  # noqa: E402
from export_classic_replay import build_replay  # noqa: E402


def test_projectile_replay_runs_real_classic_entities():
    replay = build_replay()
    scenarios = {item["scenario_id"]: item for item in replay["scenarios"]}
    assert set(scenarios) == {
        "shell_free_flight",
        "nuke_free_flight",
        "machine_gun_free_flight",
        "mirv_split",
        "missile_powered_flight",
    }
    assert scenarios["shell_free_flight"]["frames"][60]["position"] == [4.0, 1.0]
    assert len(scenarios["mirv_split"]["frames"][-1]["spawned"]) == 5
    assert scenarios["nuke_free_flight"]["frames"][1]["alive"]


def test_comparator_reports_first_field_and_rejects_semantic_difference():
    expected = build_replay()
    actual = copy.deepcopy(expected)
    actual["scenarios"][0]["frames"][4]["position"][0] += 0.01
    with pytest.raises(ReplayDifference, match=r"scenarios\[0\]\.frames\[4\]\.position\[0\]"):
        compare(expected, actual)


def test_exported_fixture_is_current():
    fixture = ROOT / "tests" / "fixtures" / "classic_replays" / "python_projectiles.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_classic_replay.py"), "--check", "--output", str(fixture)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
