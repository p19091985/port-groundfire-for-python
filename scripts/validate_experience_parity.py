#!/usr/bin/env python3
"""Run reviewable parity evidence without treating partial coverage as acceptance.

Exit 0: requested implemented checks passed (no claim of full equivalence).
Exit 1: a check failed. Exit 2: --require-complete still has missing evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/experience_parity"
PROJECT = ROOT / "versao-godot/godot"
CONTRACTS = (
    "experience_menu_check",
    "experience_audio_check",
    "classic_runtime_contract_check",
    "ai_memory_contract_check",
    "simultaneous_local_contract_check",
    "network_adapter_protocol_check",
    "server_directory_check",
    "terrain_collision_check",
    "local_match_fidelity_check",
    "test_weapon_inventory_ammo",
    "online_reliability_check",
    "browser_store_check",
    "runtime_smoke_check",
)
CAPTURE_SIZES = ((640, 480), (800, 600), (1024, 768), (1280, 960), (1280, 1024), (1600, 1200), (1920, 1080))
MISSING_EVIDENCE = (
    "Expanded full-match coverage with all weapon combinations, AI and boundary cases",
    "Paired visual review of every required screen/state/resolution",
    "Physical controllers, disconnect/reconnect and input latency measurements",
    "Audio A/B listening and event timing/loudness measurements",
    "Two-machine LAN and degraded network matrix",
    "Interactive Windows acceptance, isolated Linux export and browser platform matrix",
    "Thirty-minute performance session and final UX acceptance",
)


def source_hashes() -> dict[str, str]:
    result = {}
    for directory in ("src", "conf", "data"):
        for path in sorted((ROOT / "versao-python" / directory).rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".ini", ".json", ".png", ".wav"}:
                continue
            result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def freeze_reference() -> None:
    target = FIXTURES / "baseline.json"
    if target.exists():
        raise ValueError("Baseline already exists. Review changes explicitly before replacing it.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    write_json(target, {"schema": 1, "commit": revision, "source_hashes": source_hashes()})


def run_check(name: str, command: list[str], output: Path, env: dict[str, str], timeout: int = 90) -> dict:
    print(f"Running {name}...", flush=True)
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        log = result.stdout + result.stderr
        passed = result.returncode == 0 and "SCRIPT ERROR:" not in log and "ERROR:" not in log
        record = {"id": name, "status": "passed" if passed else "failed", "exit_code": result.returncode}
    except (OSError, subprocess.TimeoutExpired) as exc:

        def captured(value):
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""

        log = str(exc) + "\n" + captured(getattr(exc, "stdout", None)) + captured(getattr(exc, "stderr", None))
        record = {"id": name, "status": "failed", "error": str(exc)}
    log_path = output / f"{name}.log"
    log_path.write_text(log, encoding="utf-8")
    record["log"] = log_path.name
    print(f"{name}: {record['status']}", flush=True)
    return record


def report(output: Path, checks: list[dict], missing: list[str], manifest: dict) -> dict:
    failed = any(check["status"] == "failed" for check in checks)
    data = {
        "schema": 1,
        "status": "failed" if failed else "incomplete" if missing else "accepted",
        "checks": checks,
        "missing_evidence": missing,
        "manifest": manifest,
    }
    write_json(output / "report.json", data)
    rows = "".join(
        f"<tr><td>{html.escape(check['id'])}</td><td>{check['status']}</td>"
        f"<td><a href='{html.escape(check.get('log', ''), quote=True)}'>log</a></td></tr>"
        for check in checks
    )
    missing_html = "".join(f"<li>{html.escape(item)}</li>" for item in missing)
    review_link = (
        "<p><a href='visual-review.json'>Visual review index and image hashes</a></p>"
        if (output / "visual-review.json").is_file()
        else ""
    )
    gallery = []
    for python_image in sorted((output / "captures").glob("*/python/*.png")):
        godot_image = python_image.parent.parent / "godot" / python_image.name
        if godot_image.exists():
            paths = [
                html.escape(path.relative_to(output).as_posix(), quote=True) for path in (python_image, godot_image)
            ]
            gallery.append(
                f"<h3>{python_image.parent.parent.name}: {python_image.stem}</h3>"
                f"<div class='pair'><figure><figcaption>Python</figcaption><img src='{paths[0]}'></figure>"
                f"<figure><figcaption>Godot</figcaption><img src='{paths[1]}'></figure></div>"
            )
    (output / "report.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Groundfire experience parity</title>"
        "<style>body{font:16px system-ui;max-width:1400px;margin:3rem auto}"
        "td{padding:.5rem;border-bottom:1px solid #ccc}.pair{display:flex}"
        "figure{width:50%;margin:0}img{width:100%}</style>"
        f"<h1>Experience parity: {data['status']}</h1><p>Passing regressions do not certify complete equivalence.</p>"
        f"<table><tr><th>Check</th><th>Status</th><th>Evidence</th></tr>{rows}</table>"
        f"<h2>Missing acceptance evidence</h2><ul>{missing_html}</ul>"
        f"{review_link}"
        f"<h2>Paired captures (review required)</h2>{''.join(gallery)}",
        encoding="utf-8",
    )
    return data


def journey_coverage(checks: list[dict]) -> list[dict]:
    inventory = json.loads((FIXTURES / "scenarios.json").read_text(encoding="utf-8"))
    outcomes = {check["id"]: check["status"] for check in checks}
    return [
        {**journey, "check_results": {name: outcomes.get(name, "not-run") for name in journey["automated_checks"]}}
        for journey in inventory["journeys"]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot-bin", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--freeze-reference", action="store_true")
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-matrix", action="store_true", help="Capture all seven required viewport sizes")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--package", type=Path, help="Also verify this exported desktop executable in isolation")
    args = parser.parse_args()
    if args.freeze_reference:
        freeze_reference()
        print("Python baseline frozen; no runtime acceptance implied.")
        return 0
    if not args.godot_bin or not args.godot_bin.is_file():
        parser.error("--godot-bin must point to an installed Godot executable")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or ROOT / ".tmp/experience-parity" / stamp).resolve()
    output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "versao-python"), str(ROOT)))
    env["GROUNDFIRE_USERDATA_DIR"] = str(output / "python-userdata")
    # Godot computes user:// from the process environment. Isolate tests that
    # reset/rebind controls so a developer's saved profile is never overwritten.
    for key in ("APPDATA", "XDG_DATA_HOME", "XDG_CONFIG_HOME"):
        isolated = output / "godot-userdata" / key
        isolated.mkdir(parents=True, exist_ok=True)
        env[key] = str(isolated)
    godot = str(args.godot_bin.resolve())
    engine = [godot, "--headless", "--path", str(PROJECT)]
    checks = []
    baseline = json.loads((FIXTURES / "baseline.json").read_text(encoding="utf-8"))
    checks.append(
        {
            "id": "frozen-python-reference",
            "status": "passed" if baseline["source_hashes"] == source_hashes() else "failed",
        }
    )
    checks.append(
        run_check("migration-contract", [sys.executable, "scripts/validate_godot_migration_contract.py"], output, env)
    )
    checks.append(run_check("python-regressions", [sys.executable, "-m", "pytest", "-q", "tests"], output, env, 180))
    checks.append(
        run_check(
            "audio-assets",
            [sys.executable, "scripts/compare_audio_assets.py", "--output", str(output / "audio-assets.json")],
            output,
            env,
        )
    )
    checks.append(
        run_check(
            "projectile-differential",
            [
                sys.executable,
                "scripts/compare_projectile_runtimes.py",
                "--godot-bin",
                godot,
                "--output",
                str(output / "projectiles"),
            ],
            output,
            env,
        )
    )
    checks.append(
        run_check(
            "state-differential",
            [
                sys.executable,
                "scripts/compare_state_runtimes.py",
                "--godot-bin",
                godot,
                "--output",
                str(output / "states"),
            ],
            output,
            env,
            900,
        )
    )
    checks.append(
        run_check(
            "effect-geometry",
            [
                sys.executable,
                "scripts/compare_effect_geometry.py",
                "--godot-bin",
                godot,
                "--output",
                str(output / "effect-geometry"),
            ],
            output,
            env,
        )
    )
    for name in CONTRACTS:
        command = engine + ["--script", f"res://tests/{name}.gd"]
        if name == "runtime_smoke_check":
            command += ["--", "--development-tools"]  # Legacy tool screens remain supported.
        checks.append(run_check(name, command, output, env))
    checks.append(
        run_check(
            "mixed-udp",
            [sys.executable, "scripts/validate_godot_udp_integration.py", "--godot-bin", godot],
            output,
            env,
        )
    )
    checks.append(
        run_check(
            "mixed-websocket",
            [
                sys.executable,
                "scripts/validate_godot_websocket.py",
                "--godot-bin",
                godot,
                "--output",
                str(output / "websocket"),
            ],
            output,
            env,
        )
    )
    checks.append(
        run_check(
            "package-journey-source",
            engine + ["--", "--verify-package", str(output / "package-journey-source.json")],
            output,
            env,
        )
    )
    if args.package:
        checks.append(
            run_check(
                "isolated-package",
                [
                    sys.executable,
                    "scripts/validate_godot_package.py",
                    "--package",
                    str(args.package.resolve()),
                    "--output",
                    str(output / "package"),
                ],
                output,
                env,
                150,
            )
        )
    if args.capture or args.capture_matrix:
        env["EXPERIENCE_EFFECTS_DIR"] = str(output / "effects")
        checks.append(
            run_check(
                "rendered-effects",
                [
                    godot,
                    "--path",
                    str(PROJECT),
                    "--rendering-method",
                    "gl_compatibility",
                    "--script",
                    "res://tests/experience_effects_check.gd",
                ],
                output,
                env,
            )
        )
        for width, height in CAPTURE_SIZES if args.capture_matrix else ((1024, 768),):
            folder = output / "captures" / f"{width}x{height}"
            checks.append(
                run_check(
                    f"python-captures-{width}x{height}",
                    [
                        sys.executable,
                        "scripts/capture_pygame_references.py",
                        "--output-dir",
                        str(folder / "python"),
                        "--width",
                        str(width),
                        "--height",
                        str(height),
                    ],
                    output,
                    env,
                )
            )
            env["EXPERIENCE_CAPTURE_DIR"] = str(folder / "godot")
            env["EXPERIENCE_CAPTURE_WIDTH"] = str(width)
            env["EXPERIENCE_CAPTURE_HEIGHT"] = str(height)
            checks.append(
                run_check(
                    f"godot-captures-{width}x{height}",
                    [
                        godot,
                        "--path",
                        str(PROJECT),
                        "--rendering-method",
                        "gl_compatibility",
                        "--script",
                        "res://tests/experience_capture.gd",
                    ],
                    output,
                    env,
                )
            )
    if args.capture or args.capture_matrix:
        checks.append(
            run_check(
                "visual-review-index",
                [sys.executable, "scripts/build_visual_review.py", "--output", str(output), "--diffs"],
                output,
                env,
                180,
            )
        )
    manifest = {
        "python": sys.version,
        "platform": platform.platform(),
        "godot": godot,
        "godot_version": subprocess.check_output([godot, "--version"], text=True).strip(),
        "reference_commit": baseline["commit"],
        "timestamp_utc": stamp,
        "working_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines(),
    }
    write_json(output / "manifest.json", manifest)
    write_json(output / "journey-coverage.json", journey_coverage(checks))
    data = report(output, checks, list(MISSING_EVIDENCE), manifest)
    print(f"Report: {output / 'report.html'} ({data['status']})")
    if data["status"] == "failed":
        return 1
    return 2 if args.require_complete and data["status"] != "accepted" else 0


if __name__ == "__main__":
    raise SystemExit(main())
