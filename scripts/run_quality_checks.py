from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = tuple(
    path for path in ("src", "tests", "scripts", "groundfire", "groundfire_net") if (PROJECT_ROOT / path).exists()
)
LINT_TARGETS = tuple(
    path
    for path in (
        "src/groundfire",
        "groundfire",
        "groundfire_net",
        "src/main.py",
        "src/pygamebackend.py",
        "src/interface.py",
        "src/sounds.py",
        "src/font.py",
        "scripts/run_quality_checks.py",
    )
    if (PROJECT_ROOT / path).exists()
)
TYPECHECK_TARGETS = tuple(
    path
    for path in (
        "src/groundfire",
        "groundfire_net",
        "src/main.py",
        "src/pygamebackend.py",
        "src/interface.py",
        "src/sounds.py",
        "src/font.py",
    )
    if (PROJECT_ROOT / path).exists()
)


@dataclass(frozen=True)
class QualityCheck:
    name: str
    command: tuple[str, ...]
    required: bool = True
    available: bool = True


@dataclass(frozen=True)
class QualityResult:
    check: QualityCheck
    returncode: int
    stdout: str
    stderr: str
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return self.skipped or self.returncode == 0


def tool_available(*, executable: str | None = None, module_name: str | None = None) -> bool:
    if executable is not None and shutil.which(executable):
        return True
    if module_name is not None and importlib.util.find_spec(module_name) is not None:
        return True
    return False


def build_checks(python_executable: str | None = None) -> tuple[QualityCheck, ...]:
    python = python_executable or sys.executable
    ci_mode = os.environ.get("CI", "").lower() in {"1", "true", "yes"}
    checks = [
        QualityCheck(
            name="compileall",
            command=(python, "-m", "compileall", "-q", *SOURCE_DIRS),
            required=True,
        ),
        QualityCheck(
            name="unittest",
            command=(python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"),
            required=True,
        ),
        QualityCheck(
            name="ruff",
            command=(python, "-m", "ruff", "check", *LINT_TARGETS),
            required=ci_mode,
            available=tool_available(module_name="ruff", executable="ruff"),
        ),
        QualityCheck(
            name="mypy",
            command=(python, "-m", "mypy", "--explicit-package-bases", "--follow-imports=silent", *TYPECHECK_TARGETS),
            required=ci_mode,
            available=tool_available(module_name="mypy", executable="mypy"),
        ),
    ]
    return tuple(checks)


def run_check(check: QualityCheck, *, cwd: Path = PROJECT_ROOT) -> QualityResult:
    if not check.available:
        return QualityResult(check=check, returncode=0, stdout="", stderr="tool unavailable", skipped=True)

    completed = subprocess.run(
        check.command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return QualityResult(
        check=check,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def summarize_results(results: tuple[QualityResult, ...]) -> tuple[bool, str]:
    failed_required = [result for result in results if result.check.required and not result.ok]
    lines = []
    for result in results:
        if result.skipped:
            status = "SKIP"
        elif result.returncode == 0:
            status = "PASS"
        else:
            status = "FAIL"
        lines.append(f"[{status}] {result.check.name}")
    return (not failed_required, "\n".join(lines))


def main() -> int:
    results = tuple(run_check(check) for check in build_checks())
    ok, summary = summarize_results(results)
    print(summary)

    if not ok:
        for result in results:
            if result.check.required and not result.ok:
                if result.stdout:
                    print(result.stdout.strip())
                if result.stderr:
                    print(result.stderr.strip(), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
