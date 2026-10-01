"""Exercise the Godot online screen against real gateways and stalled handshakes."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Test the shipped Godot companion gateway against the unchanged Python server.
sys.path[:0] = [str(ROOT / "versao-godot/runtime/headless"), str(ROOT / "versao-python"), str(ROOT)]
from groundfire_net.websocket_gateway import WebSocketGateway, _accept_handshake, _write_text  # noqa: E402


async def validate(godot: Path, output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(ROOT / "versao-python"), str(ROOT))))
    for key in ("APPDATA", "XDG_DATA_HOME", "XDG_CONFIG_HOME"):
        folder = output / "userdata" / key
        folder.mkdir(parents=True, exist_ok=True)
        env[key] = str(folder)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        udp_port = reservation.getsockname()[1]
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "src.groundfire.server",
            "--host",
            "127.0.0.1",
            "--port",
            str(udp_port),
            "--no-discovery",
            "--headless",
            "--ticks",
            "7200",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    listeners = []
    connections = set()

    async def fault(reader, writer, mode):
        connections.add(writer)
        try:
            if mode != "http-stall":
                await _accept_handshake(reader, writer)
            if mode == "protocol":
                await _write_text(writer, json.dumps({"type": "hello", "protocol": 99, "supported_protocols": [99]}))
            await reader.read()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            connections.discard(writer)
            writer.close()

    async def listen(name, handler):
        listener = await asyncio.start_server(handler, "127.0.0.1", 0)
        listeners.append(listener)
        return f"ws://127.0.0.1:{listener.sockets[0].getsockname()[1]}/{name}"

    try:
        endpoints = {"udp": f"127.0.0.1:{udp_port}"}
        for name, options in {
            "password": {"password": "fixture-only", "max_players": 1},
            "auth": {"auth_token": "fixture-token"},
            "closed": {"closed": True},
            "banned": {"banned_players": ["GodotPlayer"]},
        }.items():
            gateway = WebSocketGateway(udp_port=udp_port, **options)
            endpoints[name] = await listen(name, gateway._handle_client)
        for mode in ("http-stall", "hello-stall", "protocol"):

            async def handler(reader, writer, fault_mode=mode):
                await fault(reader, writer, fault_mode)

            endpoints[mode] = await listen(mode, handler)
        fixture = output / "endpoints.json"
        fixture.write_text(json.dumps(endpoints, indent=2) + "\n", encoding="utf-8")
        env["GROUNDFIRE_TEST_WS_FIXTURE"] = str(fixture)
        env["GROUNDFIRE_TEST_WS_RESULTS"] = str(output / "checks.json")
        await asyncio.sleep(0.6)
        process = await asyncio.create_subprocess_exec(
            str(godot),
            "--headless",
            "--path",
            str(ROOT / "versao-godot/godot"),
            "--script",
            "res://tests/websocket_errors_check.gd",
            cwd=ROOT,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            raw, _ = await asyncio.wait_for(process.communicate(), 50)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise
        log = raw.decode("utf-8", errors="replace")
        (output / "godot.log").write_text(log, encoding="utf-8")
        print(log, end="")
        checks_path = output / "checks.json"
        checks = json.loads(checks_path.read_text(encoding="utf-8")) if checks_path.exists() else []
        passed = (
            process.returncode == 0
            and "ERROR:" not in log
            and "WebSocket screen checks passed" in log
            and bool(checks)
            and all(check["status"] == "passed" for check in checks)
        )
        (output / "report.json").write_text(
            json.dumps(
                {
                    "passed": passed,
                    "transport": "real TCP/WebSocket",
                    "fixture": "Godot companion gateway + unchanged Python UDP server + controlled faulty peers",
                    "checks": checks,
                    "gateway_sha256": hashlib.sha256(
                        (ROOT / "versao-godot/runtime/headless/groundfire_net/websocket_gateway.py").read_bytes()
                    ).hexdigest(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 0 if passed else 1
    finally:
        for listener in listeners:
            listener.close()
            await listener.wait_closed()
        for writer in tuple(connections):
            writer.close()
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot-bin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return asyncio.run(validate(args.godot_bin.resolve(), args.output.resolve()))


if __name__ == "__main__":
    raise SystemExit(main())
