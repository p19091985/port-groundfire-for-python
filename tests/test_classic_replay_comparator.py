from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from compare_classic_replay import ReplayDifference, compare  # noqa: E402
from compare_projectile_runtimes import compare_runs  # noqa: E402
from compare_state_runtimes import compare_runs as compare_state_runs  # noqa: E402
from compare_state_runtimes import scenario_batches, validate_combat_coverage, validate_cycle_coverage  # noqa: E402
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


def test_state_batches_preserve_order_and_keep_long_scenarios_whole():
    specs = [{"id": name, "ticks": ticks} for name, ticks in [("a", 2), ("b", 3), ("c", 7), ("d", 1)]]
    batches = scenario_batches(specs, max_ticks=5)
    assert [[case["id"] for case in batch] for batch in batches] == [["a", "b"], ["c"], ["d"]]
    assert [case for batch in batches for case in batch] == specs


def test_comparator_reports_first_field_and_rejects_semantic_difference():
    expected = build_replay()
    actual = copy.deepcopy(expected)
    actual["scenarios"][0]["frames"][4]["position"][0] += 0.01
    with pytest.raises(ReplayDifference, match=r"scenarios\[0\]\.frames\[4\]\.position\[0\]"):
        compare(expected, actual)


def test_discrete_fields_cannot_hide_inside_float_tolerance():
    compare({"tick": 4}, {"tick": 4.0})  # Godot JSON numbers are floats.
    with pytest.raises(ReplayDifference, match="discrete"):
        compare({"tick": 4}, {"tick": 4.000001})
    with pytest.raises(ReplayDifference):
        compare({"alive": True}, {"alive": 1})


@pytest.mark.parametrize("tolerance", [-1, float("nan"), float("inf")])
def test_invalid_tolerance_is_rejected(tolerance):
    with pytest.raises(ValueError):
        compare(1.0, 1.0, tolerance=tolerance)


def test_coordinate_tolerance_does_not_relax_events_or_other_fields():
    expected = {"position": [1.0, 2.0], "fuel": 3.0, "tick": 4, "alive": True}
    rounded = {**expected, "position": [1.000012, 2.0]}
    compare(expected, rounded, field_tolerances={"position": 1.5e-5})
    for key, value in (("fuel", 3.000012), ("tick", 4.000001), ("alive", False)):
        with pytest.raises(ReplayDifference):
            compare(expected, {**rounded, key: value}, field_tolerances={"position": 1.5e-5})


@pytest.mark.parametrize("mutation", ["missing", "extra", "reordered", "schema", "event"])
@pytest.mark.parametrize("runner", [compare_runs, compare_state_runs])
def test_differential_report_rejects_missing_cases_and_discrete_events(mutation, runner):
    expected = {
        "schema": 1,
        "scenarios": [
            {"id": "a", "frames": [{"tick": 0, "alive": True}]},
            {"id": "b", "frames": [{"tick": 0, "alive": True}]},
        ],
        "timing": [],
    }
    actual = copy.deepcopy(expected)
    if runner is compare_state_runs:
        del expected["timing"]
        del actual["timing"]
    if mutation == "missing":
        actual["scenarios"].pop()
    elif mutation == "extra":
        actual["scenarios"].append({"id": "unexpected", "frames": []})
    elif mutation == "reordered":
        actual["scenarios"].reverse()
    elif mutation == "schema":
        actual["schema"] = 2
    else:
        actual["scenarios"][0]["frames"][0]["alive"] = False
    assert any(item["status"] == "failed" for item in runner(expected, actual))


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


def test_post_crater_body_tilt_tolerance_keeps_damage_and_events_strict():
    expected = {
        "schema": 1,
        "scenarios": [
            {"id": "combat", "frames": [{"body_angle": 12.0, "angle": 3.0, "health": 60.0, "tick": 262, "alive": True}]}
        ],
    }
    actual = copy.deepcopy(expected)
    frame = actual["scenarios"][0]["frames"][0]
    frame["body_angle"] += 0.000005
    assert compare_state_runs(expected, actual)[0]["status"] == "passed"
    for key, value in (
        ("body_angle", 12.0005),
        ("angle", 3.0005),
        ("health", 60.0005),
        ("tick", 263),
        ("alive", False),
    ):
        changed = copy.deepcopy(actual)
        changed["scenarios"][0]["frames"][0][key] = value
        assert compare_state_runs(expected, changed)[0]["status"] == "failed"


@pytest.mark.parametrize("mutation", ["truncated", "no_purchase", "no_shop"])
def test_cycle_requires_real_purchase_and_next_round(mutation):
    spec = {"id": "cycle"}
    frames = [
        {"phase": "score", "round": 1, "stocks": [[0]]},
        {"phase": "shop", "round": 1, "stocks": [[0]]},
        {"phase": "shop", "round": 1, "stocks": [[50]]},
        {"phase": "aim", "round": 2, "stocks": [[50]]},
    ]
    validate_cycle_coverage(spec, frames)
    if mutation == "truncated":
        frames.pop()
    elif mutation == "no_purchase":
        for frame in frames:
            frame["stocks"] = [[0]]
    else:
        frames = [frame for frame in frames if frame["phase"] != "shop"]
    with pytest.raises(ValueError):
        validate_cycle_coverage(spec, frames)


def test_audio_comparison_rejects_missing_duplicate_or_late_effect():
    expected = {
        "schema": 1,
        "scenarios": [
            {"id": "audio", "frames": [{"tick": 0, "audio_one_shots": [0, 0]}, {"tick": 1, "audio_one_shots": []}]}
        ],
    }
    for sounds in ([0], [0, 0, 0], []):
        actual = copy.deepcopy(expected)
        actual["scenarios"][0]["frames"][0]["audio_one_shots"] = sounds
        actual["scenarios"][0]["frames"][1]["audio_one_shots"] = [0] if not sounds else []
        assert compare_state_runs(expected, actual)[0]["status"] == "failed"


@pytest.mark.parametrize("loops", [[4, 8], [4, 4, 8, 8], []])
def test_loop_comparison_requires_each_concurrent_source(loops):
    expected = {"schema": 1, "scenarios": [{"id": "loops", "frames": [{"tick": 1, "audio_loops": [4, 4, 8]}]}]}
    actual = copy.deepcopy(expected)
    actual["scenarios"][0]["frames"][0]["audio_loops"] = loops
    assert compare_state_runs(expected, actual)[0]["status"] == "failed"


@pytest.mark.parametrize("projectiles", [[], [{"owner": 1, "kind": "missile"}], [{"owner": 0, "kind": "shell"}]])
def test_combat_coverage_rejects_absent_wrong_owner_or_wrong_weapon(projectiles):
    spec = {"id": "guided", "required_shots": [{"owner": 0, "kind": "missile"}]}
    validate_combat_coverage(spec, [{"projectiles": spec["required_shots"]}])
    with pytest.raises(ValueError, match="required projectile not observed"):
        validate_combat_coverage(spec, [{"projectiles": projectiles}])
