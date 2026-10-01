#!/usr/bin/env python3
"""Verify a desktop export alone in a fresh directory with spaces and accents.

The package must use an embedded PCK, as in the repository's export presets.
Keeps the isolated copy and reports its path for investigation and reruns.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


def validate(package: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    isolated = Path(tempfile.mkdtemp(prefix="Groundfire isolado acentuação ")).resolve()
    executable = isolated / package.name
    shutil.copy2(package, executable)
    env = os.environ.copy()
    for key in ("APPDATA", "XDG_DATA_HOME", "XDG_CONFIG_HOME"):
        directory = isolated / "userdata" / key
        directory.mkdir(parents=True, exist_ok=True)
        env[key] = str(directory)
    checks = []
    for name in ("first-use", "restart"):
        target = isolated / f"{name}.json"
        result = subprocess.run(
            [str(executable), "--headless", "--", "--verify-package", str(target)],
            cwd=isolated,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        log = result.stdout + result.stderr
        (output / f"{name}.log").write_text(log, encoding="utf-8")
        evidence = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
        passed = result.returncode == 0 and "ERROR:" not in log and evidence.get("status") == "passed"
        if name == "restart":
            saved = checks[0]["evidence"].get("saved_resolution")
            passed = passed and saved is not None and evidence.get("initial_resolution") == saved
        checks.append(
            {
                "id": name,
                "status": "passed" if passed else "failed",
                "exit_code": result.returncode,
                "evidence": evidence,
            }
        )
    report = {
        "schema": 1,
        "platform": platform.platform(),
        "copy_directory": str(isolated),
        "package_sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
        "checks": checks,
        "status": "passed" if all(check["status"] == "passed" for check in checks) else "failed",
        "limitations": [
            "Automated headless journey with injected fixture deaths, not interactive acceptance",
            "Uses installed OS libraries; not a clean-machine certification",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.package.is_file():
        parser.error("--package must identify an exported desktop executable")
    result = validate(args.package.resolve(), args.output.resolve())
    print(f"Isolated package: {result['status']} ({result['copy_directory']})")
    return int(result["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
