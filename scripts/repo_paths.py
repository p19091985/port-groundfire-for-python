from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _path_from_env(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    if value:
        return Path(value).resolve()
    return default


def godot_project_dir() -> Path:
    configured = _path_from_env("GODOT_PROJECT_DIR", PROJECT_ROOT / "versao-godot" / "godot")
    if (configured / "project.godot").exists():
        return configured
    legacy = PROJECT_ROOT / "godot"
    if (legacy / "project.godot").exists():
        return legacy
    return configured


def python_version_dir() -> Path:
    configured = _path_from_env("PYTHON_VERSION_DIR", PROJECT_ROOT / "versao-python")
    if (configured / "src").exists():
        return configured
    legacy = PROJECT_ROOT
    if (legacy / "src").exists():
        return legacy
    return configured


def python_src_dir() -> Path:
    return _path_from_env("PYTHON_SRC_DIR", python_version_dir() / "src")


def python_conf_dir() -> Path:
    return _path_from_env("PYTHON_CONF_DIR", python_version_dir() / "conf")


def python_data_dir() -> Path:
    return _path_from_env("PYTHON_DATA_DIR", python_version_dir() / "data")


def build_dir() -> Path:
    return _path_from_env("BUILD_DIR", PROJECT_ROOT / "build")


def dist_dir() -> Path:
    return _path_from_env("DIST_DIR", PROJECT_ROOT / "dist")


def groundfire_net_dir() -> Path:
    return _path_from_env("GROUNDFIRE_NET_DIR", PROJECT_ROOT / "groundfire_net")


def pythonpath_entries() -> list[Path]:
    return [python_version_dir(), PROJECT_ROOT]


def relative_to_root(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()
