from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.repo_paths import PROJECT_ROOT, python_version_dir, relative_to_root
except ModuleNotFoundError:
    from repo_paths import PROJECT_ROOT, python_version_dir, relative_to_root


PYTHON_VERSION_DIR = python_version_dir()


def _rel(path: Path) -> str:
    return relative_to_root(path)


SOURCE_DIRS = tuple(
    _rel(path)
    for path in (
        PYTHON_VERSION_DIR / "src",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "scripts",
        PYTHON_VERSION_DIR / "groundfire",
        PROJECT_ROOT / "groundfire_net",
    )
    if path.exists()
)
LINT_TARGETS = tuple(
    _rel(path)
    for path in (
        PYTHON_VERSION_DIR / "src" / "groundfire",
        PYTHON_VERSION_DIR / "groundfire",
        PROJECT_ROOT / "groundfire_net",
        PYTHON_VERSION_DIR / "src" / "main.py",
        PYTHON_VERSION_DIR / "src" / "pygamebackend.py",
        PYTHON_VERSION_DIR / "src" / "interface.py",
        PYTHON_VERSION_DIR / "src" / "sounds.py",
        PYTHON_VERSION_DIR / "src" / "font.py",
        PROJECT_ROOT / "scripts" / "run_quality_checks.py",
        PROJECT_ROOT / "scripts" / "verify_godot_hosted_deployment.py",
    )
    if path.exists()
)
TYPECHECK_TARGETS = tuple(
    _rel(path)
    for path in (
        PYTHON_VERSION_DIR / "src" / "groundfire",
        PROJECT_ROOT / "groundfire_net",
        PYTHON_VERSION_DIR / "src" / "main.py",
        PYTHON_VERSION_DIR / "src" / "pygamebackend.py",
        PYTHON_VERSION_DIR / "src" / "interface.py",
        PYTHON_VERSION_DIR / "src" / "sounds.py",
        PYTHON_VERSION_DIR / "src" / "font.py",
    )
    if path.exists()
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

    env = os.environ.copy()
    pythonpath = os.pathsep.join((str(PYTHON_VERSION_DIR), str(PROJECT_ROOT)))
    if env.get("PYTHONPATH"):
        pythonpath = os.pathsep.join((pythonpath, env["PYTHONPATH"]))
    env["PYTHONPATH"] = pythonpath

    completed = subprocess.run(
        check.command,
        cwd=cwd,
        env=env,
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
