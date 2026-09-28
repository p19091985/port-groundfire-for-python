from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYTHON_EDITION = REPOSITORY_ROOT / "versao-python"
if str(PYTHON_EDITION) not in sys.path:
    sys.path.insert(0, str(PYTHON_EDITION))

from src.groundfire.service_client import GroundfireServiceClient  # noqa: E402


def test_service_source_runs_after_isolated_copy(tmp_path: Path):
    source_root = Path(__file__).resolve().parents[1]
    isolated = tmp_path / "Pasta com espaços" / "servico-externo"
    isolated.mkdir(parents=True)
    shutil.copytree(source_root / "src", isolated / "src")
    shutil.copytree(source_root / "conf", isolated / "conf")
    shutil.copy2(source_root / "config.example.toml", isolated / "config.example.toml")
    shutil.copy2(source_root / "runtime-manifest.json", isolated / "runtime-manifest.json")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(isolated / "src")
    env.pop("GF_SERVICE_CONFIG", None)
    completed = subprocess.run(
        [sys.executable, "-m", "gf_service", "check"],
        cwd=isolated,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (isolated / "data" / "service.sqlite3").is_file()
    assert (isolated / "src" / "groundfire" / "app" / "server.py").is_file()
    assert (isolated / "src" / "groundfire_net" / "websocket_gateway.py").is_file()
    for path in (isolated / "src" / "gf_service").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "src.groundfire" not in text
        assert "versao-python" not in text
        assert "versao-godot" not in text


def test_isolated_copy_starts_and_allocates_a_real_match(tmp_path: Path):
    source_root = Path(__file__).resolve().parents[1]
    isolated = tmp_path / "Cópia isolada" / "servico-externo"
    shutil.copytree(source_root / "src", isolated / "src")
    shutil.copytree(source_root / "conf", isolated / "conf")
    shutil.copy2(source_root / "runtime-manifest.json", isolated / "runtime-manifest.json")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    (isolated / "config.toml").write_text(
        f'[service]\nbind="127.0.0.1"\nport={port}\npublic_base_url="http://127.0.0.1:{port}"\n'
        '[storage]\ndatabase="data/service.sqlite3"\n'
        '[matches]\nmax_workers=1\nworker_bind="127.0.0.1"\nworker_public_host="127.0.0.1"\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(isolated / "src")
    process = subprocess.Popen(
        [sys.executable, "-m", "gf_service", "start"],
        cwd=isolated,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    client = GroundfireServiceClient(f"http://127.0.0.1:{port}", timeout=0.25)
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            try:
                if client.request("GET", "/readyz", authenticated=False).data is None:
                    break
            except Exception:
                time.sleep(0.05)
            else:
                break
        assert process.poll() is None
        client.timeout = 8.0
        session = client.guest("Standalone")
        lobby = client.create_lobby(
            name="Isolated match",
            visibility="public",
            capacity=2,
            rounds=5,
            map_id="classic",
            seed=31,
            bots=1,
        )
        client.set_lobby_ready(lobby["lobby_id"], lobby["revision"])
        match = client.start_lobby(lobby["lobby_id"], lobby["revision"])
        assert session["user"]["display_name"] == "Standalone"
        assert match["state"] == "active"
        assert match["websocket_url"].startswith("ws://127.0.0.1:")
    finally:
        subprocess.run(
            [sys.executable, "-m", "gf_service", "stop"],
            cwd=isolated,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=8,
            check=False,
        )
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=3)
