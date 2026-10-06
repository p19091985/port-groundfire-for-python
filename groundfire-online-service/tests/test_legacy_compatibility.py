from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from groundfire_net.browser import ServerListEntry
from groundfire_net.master import MasterQuery, MasterServerAddress, MasterServerClient
from groundfire_net.websocket_gateway import validate_join_token

from gf_service.app import create_app
from gf_service.config import Settings


def test_unified_http_listener_serves_static_legacy_directory_and_tokens(tmp_path: Path):
    directory = tmp_path / "legacy-directory.json"
    directory.write_text(
        json.dumps(
            {
                "schema": 1,
                "servers": [
                    {
                        "name": "Legacy Arena",
                        "game": "Groundfire",
                        "players": "1/8",
                        "map": "classic",
                        "latency": "20ms",
                        "source": "online",
                        "endpoint": "wss://legacy.example/game",
                        "passworded": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    settings = Settings(
        root=tmp_path,
        database=str(tmp_path / "service.sqlite3"),
        legacy_directory_path=str(directory),
        legacy_session_secret="legacy-test-secret",
        legacy_master_enabled=False,
    )
    with TestClient(create_app(settings)) as client:
        features = client.get("/api/v1/capabilities").json()["data"]["features"]
        assert features["legacy_directory"] is True
        assert features["legacy_session_tokens"] is True
        assert features["legacy_udp_master"] is False

        response = client.get("/servers.json")
        assert response.status_code == 200
        assert response.json()["servers"][0]["name"] == "Legacy Arena"
        assert response.headers["etag"].startswith('"')
        head = client.head("/servers.json")
        assert head.status_code == 200
        assert not head.content
        assert head.headers["content-length"] == response.headers["content-length"]

        token = client.get("/session-token.json", params={"player_name": "Legacy Player"})
        assert token.status_code == 200
        payload = token.json()
        assert payload["auth_token"].startswith("gf1.")
        assert validate_join_token(payload["auth_token"], "legacy-test-secret", "Legacy Player")
        assert token.headers["cache-control"] == "no-store"


def test_unified_service_starts_and_stops_protocol_one_udp_master(tmp_path: Path):
    settings = Settings(
        root=tmp_path,
        database=str(tmp_path / "service.sqlite3"),
        legacy_master_enabled=True,
        legacy_master_port=0,
    )
    app = create_app(settings)
    with TestClient(app) as http:
        health = http.get("/healthz").json()
        port = int(health["legacy_master"]["port"])
        assert health["legacy_master"]["running"] is True
        assert port > 0

        client = MasterServerClient()
        address = MasterServerAddress("127.0.0.1", port)
        entry = ServerListEntry(
            name="Registered Legacy Server",
            host="127.0.0.1",
            port=27015,
            player_count=1,
            max_players=8,
            source="internet",
        )
        try:
            registered = client.register(address, entry, timeout=0.5)
            assert registered is not None
            found = client.query(address, MasterQuery(), timeout=0.5)
            assert [item.name for item in found] == ["Registered Legacy Server"]
        finally:
            client.close()
    assert app.state.legacy_master.running is False
