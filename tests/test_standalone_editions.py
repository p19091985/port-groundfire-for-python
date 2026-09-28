"""ST00-ST07: prova isolada das edicoes standalone (fonte isolada).

Copia a pasta versao-python/ inteira e, em outro ambiente, a pasta
versao-godot/ inteira para um diretorio temporario, sem a raiz do
repositorio nem a outra edicao. Falha se uma pasta tocar a outra ou
a raiz antiga (imports, ../, .venv externo, tools/ irma).

Nao exige Godot, Pygame, rede ou build de binarios: e verificacao
estatica + imports do nucleo LAN com PYTHONPATH vazio e rede negada
no teste local. Binarios portateis (ST02/ST06) sao verificados por
scripts/generate_runtime_manifest.py + ZIPs quando gerados.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_EDITION = REPO_ROOT / "versao-python"
GODOT_EDITION = REPO_ROOT / "versao-godot"

FORBIDDEN_PYTHON_SNIPPETS = (
    "../tools/godot",
    "../versao-python",
    "../versao-godot",
    "../groundfire_net",
    "../.venv",
    "pip install -e \"$PROJECT_DIR\"",
    'pip install -e "$PROJECT_DIR"',
    "GODOT_LAUNCHER_ROOT/versao-python",
    "GODOT_LAUNCHER_ROOT/.venv",
    "res://../.venv",
)

FORBIDDEN_GODOT_SNIPPETS = (
    "../tools/godot",
    "../versao-python",
    "../.venv",
    "GODOT_LAUNCHER_ROOT/versao-python",
    "GODOT_LAUNCHER_ROOT/.venv",
    "res://../.venv",
    "../../build",
)


def _copy_edition(src: Path, tmp_path: Path) -> Path:
    dest = tmp_path / src.name
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc", "logs", ".godot", "build"),
    )
    return dest


SKIP_AUDIT_NAMES = {"README.md", "runtime-manifest.json", ".gitkeep"}


def _text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in SKIP_AUDIT_NAMES or path.suffix.lower() in {".png", ".wav", ".ogg", ".mp3", ".ttf", ".pck", ".x86_64", ".exe"}:
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def test_python_edition_copies_without_root_or_sibling(tmp_path):
    isolated = _copy_edition(PYTHON_EDITION, tmp_path)
    assert (isolated / "pyproject.toml").is_file()
    assert (isolated / "requirements.lock").is_file()
    assert (isolated / "groundfire_net").is_dir()
    assert (isolated / "run_game.sh").is_file()
    assert (isolated / "run_game.ps1").is_file()
    assert (isolated / "run_game.bat").is_file()

    offenders: list[str] = []
    for path, text in _text_files(isolated):
        rel = path.relative_to(isolated).as_posix()
        # run_game.* da raiz nao existe aqui; launchers devem ser locais.
        for snippet in FORBIDDEN_PYTHON_SNIPPETS:
            if snippet in text:
                offenders.append(f"{rel}: {snippet!r}")
    assert not offenders, "versao-python/ toca raiz/irma:\n" + "\n".join(offenders)


def test_godot_edition_copies_without_root_or_sibling(tmp_path):
    isolated = _copy_edition(GODOT_EDITION, tmp_path)
    assert (isolated / "godot" / "project.godot").is_file()
    assert (isolated / "scripts" / "launcher_common.sh").is_file()

    offenders: list[str] = []
    for path, text in _text_files(isolated):
        rel = path.relative_to(isolated).as_posix()
        for snippet in FORBIDDEN_GODOT_SNIPPETS:
            if snippet in text:
                offenders.append(f"{rel}: {snippet!r}")
    assert not offenders, "versao-godot/ toca raiz/irma:\n" + "\n".join(offenders)


def test_python_core_imports_without_repo_root(tmp_path, monkeypatch):
    isolated = _copy_edition(PYTHON_EDITION, tmp_path)
    monkeypatch.setenv("PYTHONPATH", "")
    monkeypatch.syspath_prepend(str(isolated))
    monkeypatch.syspath_prepend(str(isolated / "src"))
    for mod in [m for m in list(sys.modules) if m.startswith(("src.", "groundfire", "groundfire_net"))]:
        del sys.modules[mod]
    import groundfire_net  # noqa: F401
    from groundfire_net import codec, discovery, transport  # noqa: F401
    from groundfire.network import messages  # noqa: F401


def test_edition_userdata_dirs_exist_and_are_documented():
    for edition in (PYTHON_EDITION, GODOT_EDITION):
        assert (edition / "userdata").is_dir(), f"{edition.name}/userdata ausente (ST05)"
        assert (edition / "README.md").is_file(), f"{edition.name}/README.md ausente (ST08)"


def _import_edition_paths(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO_ROOT / "versao-python" / "src"))
    for mod in [m for m in list(sys.modules) if m == "src" or m.startswith("src.")]:
        del sys.modules[mod]
    from src.groundfire.core import paths

    return paths


def test_edition_paths_honor_env_and_frozen(monkeypatch, tmp_path):
    paths = _import_edition_paths(monkeypatch)
    monkeypatch.delenv("GROUNDFIRE_EDITION_DIR", raising=False)
    monkeypatch.delenv("GROUNDFIRE_USERDATA_DIR", raising=False)
    assert paths.edition_dir() == PYTHON_EDITION
    assert paths.userdata_dir() == PYTHON_EDITION / "userdata"

    monkeypatch.setenv("GROUNDFIRE_EDITION_DIR", str(tmp_path / "ed"))
    monkeypatch.setenv("GROUNDFIRE_USERDATA_DIR", str(tmp_path / "ud"))
    assert paths.edition_dir() == tmp_path / "ed"
    assert paths.userdata_dir() == tmp_path / "ud"

    monkeypatch.delenv("GROUNDFIRE_EDITION_DIR")
    monkeypatch.delenv("GROUNDFIRE_USERDATA_DIR")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    fake_exe = tmp_path / "ed" / "runtime" / "windows" / "Groundfire.exe"
    monkeypatch.setattr(sys, "executable", str(fake_exe), raising=False)
    assert paths.edition_dir() == tmp_path / "ed"
    assert paths.userdata_dir() == tmp_path / "ed" / "userdata"


def test_server_book_uses_userdata_and_migrates_once(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(REPO_ROOT / "versao-python" / "src"))
    for mod in [m for m in list(sys.modules) if m == "src" or m.startswith("src.")]:
        del sys.modules[mod]
    from src.groundfire.network.browser import default_server_book_path

    root = tmp_path / "ed"
    (root / "conf").mkdir(parents=True)
    legacy = root / "conf" / "servers.sqlite3"
    legacy.write_bytes(b"legacy-book")

    monkeypatch.delenv("GROUNDFIRE_USERDATA_DIR", raising=False)
    assert default_server_book_path(root) == legacy

    monkeypatch.setenv("GROUNDFIRE_USERDATA_DIR", str(tmp_path / "ud"))
    target = tmp_path / "ud" / "servers.sqlite3"
    assert default_server_book_path(root) == target
    assert target.read_bytes() == b"legacy-book"

    target.write_bytes(b"user-edited")
    assert default_server_book_path(root) == target
    assert target.read_bytes() == b"user-edited"


@pytest.mark.skipif(os.name != "nt", reason="launcher .bat (Windows)")
def test_run_game_bat_uses_binary_without_venv(tmp_path):
    runtime_bin = PYTHON_EDITION / "runtime" / "windows" / "Groundfire.exe"
    if not runtime_bin.is_file():
        pytest.skip("binarios portateis nao gerados (ST02)")
    mini = tmp_path / "mini"
    (mini / "userdata").mkdir(parents=True)
    shutil.copy2(PYTHON_EDITION / "run_game.bat", mini / "run_game.bat")
    shutil.copytree(PYTHON_EDITION / "runtime", mini / "runtime")
    env = dict(os.environ, PYTHONPATH="")
    env.pop("GROUNDFIRE_USERDATA_DIR", None)
    env.pop("GROUNDFIRE_FORCE_SOURCE", None)
    completed = subprocess.run(
        ["cmd", "/c", str(mini / "run_game.bat"), "--help"],
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
        cwd="C:\\",
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert "usage:" in completed.stdout.lower()
    assert not (mini / ".venv").exists()


def test_vendored_copies_match_sources():
    for script in (
        PYTHON_EDITION / "scripts" / "vendor_groundfire_net.py",
        GODOT_EDITION / "scripts" / "vendor_headless.py",
    ):
        completed = subprocess.run(
            [sys.executable, str(script), "--check"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(REPO_ROOT),
        )
        assert completed.returncode == 0, f"{script.name}:\n" + completed.stderr + completed.stdout
