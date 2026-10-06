from __future__ import annotations

import json
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[2]
PYTHON_EDITION = ROOT / "versao-python"
if str(PYTHON_EDITION) not in sys.path:
    sys.path.insert(0, str(PYTHON_EDITION))

from gf_service.app import create_app  # noqa: E402
from gf_service.config import Settings  # noqa: E402
from src.groundfire.service_client import GroundfireServiceClient, ServiceClientError  # noqa: E402


def test_python_adapter_runs_complete_http_journey(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    settings = Settings(
        root=tmp_path,
        database=str(tmp_path / "adapter.sqlite3"),
        port=port,
        public_base_url=f"http://127.0.0.1:{port}",
        legacy_master_enabled=False,
    )
    server = uvicorn.Server(uvicorn.Config(create_app(settings), host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    assert server.started
    try:
        client = GroundfireServiceClient(f"http://127.0.0.1:{port}")
        session = client.register("adapter_user", "Adapter", "adapter-password-123")
        assert session["user"]["handle"] == "adapter_user"
        lobby = client.create_lobby(
            name="Adapter room", visibility="public", capacity=4, rounds=10, map_id="classic", seed=1, bots=1
        )
        assert lobby["leader_id"] == session["user"]["user_id"]
        assert (
            client.request("GET", "/api/v1/servers", authenticated=False).data["items"][0]["server_id"]
            == lobby["lobby_id"]
        )
        ready = client.set_lobby_ready(lobby["lobby_id"], lobby["revision"])
        assert ready["members"][0]["ready_revision"] == lobby["revision"]
        match = client.start_lobby(lobby["lobby_id"], lobby["revision"])
        assert match["state"] == "active"
        admission = client.admission_ticket(match["reservation_id"], "ws")
        assert admission["endpoint"].startswith("ws://")
        assert admission["admission_ticket"].startswith("gf1.")
        with connect(admission["endpoint"], open_timeout=3, close_timeout=1) as websocket:
            websocket.send(json.dumps({"type": "hello", "protocol": 2}))
            assert json.loads(websocket.recv(timeout=3))["type"] == "hello"
            websocket.send(
                json.dumps(
                    {
                        "type": "join",
                        "protocol": 2,
                        "player_name": admission["player_name"],
                        "auth_token": admission["admission_ticket"],
                    }
                )
            )
            while json.loads(websocket.recv(timeout=3)).get("type") != "snapshot":
                pass
        with connect(admission["endpoint"], open_timeout=3, close_timeout=1) as websocket:
            websocket.send(json.dumps({"type": "hello", "protocol": 2}))
            assert json.loads(websocket.recv(timeout=3))["type"] == "hello"
            websocket.send(
                json.dumps(
                    {
                        "type": "join",
                        "protocol": 2,
                        "player_name": admission["player_name"],
                        "auth_token": admission["admission_ticket"],
                    }
                )
            )
            rejected = json.loads(websocket.recv(timeout=3))
            assert rejected["type"] == "error"
            assert rejected["message"] == "authentication_failed"
        try:
            client.login("adapter_user", "wrong-password")
        except ServiceClientError as exc:
            assert exc.code == "invalid_credentials"
            assert exc.status == 401
        else:
            raise AssertionError("invalid login unexpectedly succeeded")
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        assert not thread.is_alive()
