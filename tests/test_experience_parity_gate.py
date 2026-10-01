from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_experience_parity import journey_coverage, report, run_check  # noqa: E402


def test_successful_process_with_godot_assertion_is_a_failed_check(tmp_path):
    result = run_check(
        "assertion", [sys.executable, "-c", "print('SCRIPT ERROR: Assertion failed.')"], tmp_path, os.environ.copy()
    )
    assert result["exit_code"] == 0
    assert result["status"] == "failed"


def test_passing_regressions_cannot_certify_missing_acceptance(tmp_path):
    result = report(tmp_path, [{"id": "regression", "status": "passed"}], ["Physical controller test"], {})
    assert result["status"] == "incomplete"
    assert "Physical controller test" in (tmp_path / "report.html").read_text(encoding="utf-8")


def test_journey_coverage_keeps_unexecuted_requirements_visible():
    journeys = journey_coverage([{"id": "experience_menu_check", "status": "passed"}])
    assert [item["id"] for item in journeys] == [f"UX-{index:02}" for index in range(1, 13)]
    assert all(item["acceptance"] == "pending" for item in journeys)
    assert journeys[0]["check_results"]["experience_menu_check"] == "passed"
    assert journeys[-1]["check_results"]["browser_store_check"] == "not-run"
