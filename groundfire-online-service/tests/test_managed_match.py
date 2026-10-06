from __future__ import annotations

import json
import time

from test_api_journeys import headers, register
from websockets.sync.client import connect


def test_lobby_starts_real_worker_and_accepts_authenticated_websocket_player(client):
    host = register(client, "managed_host")
    lobby = client.post(
        "/api/v1/lobbies",
        headers=headers(host),
        json={
            "name": "Managed match",
            "visibility": "public",
            "capacity": 2,
            "rounds": 5,
            "map_id": "classic",
            "seed": 19,
            "bots": 1,
        },
    ).json()["data"]
    ready = client.put(
        f"/api/v1/lobbies/{lobby['lobby_id']}/members/me/ready",
        headers=headers(host),
        json={"revision": lobby["revision"], "ready": True},
    )
    assert ready.status_code == 200, ready.text

    started = client.post(
        f"/api/v1/lobbies/{lobby['lobby_id']}/start",
        headers=headers(host),
        json={"revision": lobby["revision"]},
    )
    assert started.status_code == 201, started.text
    match = started.json()["data"]
    assert match["state"] == "active"
    assert match["websocket_url"].startswith("ws://")
    assert "session_secret" not in match

    ticket = client.post(
        f"/api/v1/reservations/{match['reservation_id']}/admission-tickets",
        headers=headers(host),
        json={"transport": "ws"},
    )
    assert ticket.status_code == 200, ticket.text
    admission = ticket.json()["data"]
    assert admission["match_id"] == match["match_id"]
    assert admission["protocol_version"] == 2

    with connect(admission["endpoint"], open_timeout=3, close_timeout=1) as websocket:
        websocket.send(json.dumps({"type": "hello", "protocol": 2}))
        hello = json.loads(websocket.recv(timeout=3))
        assert hello["type"] == "hello"
        assert hello["auth_required"] is True
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
        deadline = time.monotonic() + 4
        snapshot = None
        while time.monotonic() < deadline:
            message = json.loads(websocket.recv(timeout=3))
            if message.get("type") == "snapshot":
                snapshot = message
                break
        assert snapshot is not None
        assert snapshot["state"]["joined"] is True
        assert snapshot["state"]["player_name"] == admission["player_name"]
        assert snapshot["state"]["match_snapshot"]["seed"] == 19
        initial_tick = snapshot["state"]["match_snapshot"]["simulation_tick"]
        websocket.send(
            json.dumps(
                {
                    "type": "lobby_set_ready",
                    "protocol": 2,
                    "request_id": "ready-1",
                    "ready": True,
                }
            )
        )
        ready_accepted = False
        advanced_tick = False
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and not (ready_accepted and advanced_tick):
            message = json.loads(websocket.recv(timeout=3))
            if message.get("type") == "command_result" and message.get("request_id") == "ready-1":
                ready_accepted = message.get("accepted") is True
            if message.get("type") == "snapshot":
                advanced_tick = message["state"]["match_snapshot"]["simulation_tick"] > initial_tick
        assert ready_accepted
        assert advanced_tick

        websocket.send(
            json.dumps(
                {
                    "type": "input",
                    "protocol": 2,
                    "sequence": 1,
                    "command": {"aim_right": True, "power_up": True},
                }
            )
        )
        websocket.send(json.dumps({"type": "ping", "protocol": 2, "sequence": 7, "client_time_msec": 10}))
        deadline = time.monotonic() + 3
        pong = None
        while time.monotonic() < deadline:
            message = json.loads(websocket.recv(timeout=3))
            if message.get("type") == "pong":
                pong = message
                break
        assert pong is not None
        assert pong["sequence"] == 7
