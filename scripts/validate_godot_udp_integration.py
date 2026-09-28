#!/usr/bin/env python3
"""Run a real Godot client against the authoritative Python UDP server."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GODOT_PROJECT = ROOT / "versao-godot" / "godot"


def _free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _default_godot_bin() -> Path:
    candidates = (
        ROOT / "tools" / "godot" / "Godot_v4.6.2-stable_linux.x86_64",
        ROOT / "tools" / "godot" / "Godot_v4.6.2-stable_win64_console.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Godot 4.6.2 executable not found; pass --godot-bin or set GODOT_BIN")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot-bin", default=os.environ.get("GODOT_BIN", ""))
    args = parser.parse_args()
    godot_bin = Path(args.godot_bin) if args.godot_bin else _default_godot_bin()
    game_port = _free_udp_port()
    discovery_port = _free_udp_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "versao-python")
    env["GROUNDFIRE_TEST_UDP_ENDPOINT"] = f"127.0.0.1:{game_port}"
    env["GROUNDFIRE_TEST_DISCOVERY_PORT"] = str(discovery_port)
    server_command = [
        sys.executable,
        "-m",
        "src.groundfire.server",
        "--host",
        "127.0.0.1",
        "--port",
        str(game_port),
        "--discovery-port",
        str(discovery_port),
        "--ticks",
        "1800",
        "--rounds",
        "2",
        "--server-name",
        "GodotUDPIntegration",
        "--headless",
    ]
    server = subprocess.Popen(
        server_command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(0.6)
        for script in (
            "res://tests/udp_python_integration_check.gd",
            "res://tests/udp_spectator_integration_check.gd",
        ):
            result = subprocess.run(
                [
                    str(godot_bin),
                    "--headless",
                    "--path",
                    str(GODOT_PROJECT),
                    "--script",
                    script,
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=12,
                check=False,
            )
            print(result.stdout, end="")
            if result.returncode != 0:
                return result.returncode
            if "SCRIPT ERROR:" in result.stdout or "ERROR:" in result.stdout:
                print(f"Godot reported a script/runtime error during {script}.", file=sys.stderr)
                return 1
        print("Godot/Python native UDP player, resume, discovery, spectator and chat integration passed.")
        return 0
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=3)
        if server.returncode not in {0, None, -15, 1}:
            output = server.stdout.read() if server.stdout is not None else ""
            if output:
                print(output, file=sys.stderr, end="")


if __name__ == "__main__":
    raise SystemExit(main())
