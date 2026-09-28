from __future__ import annotations

from conftest import headers, register


def test_account_friend_presence_and_event_socket(client):
    ana = register(client, "ana_player")
    bia = register(client, "bia_player")
    request = client.post(
        "/api/v1/friend-requests",
        headers=headers(ana),
        json={"target_user_id": bia["user"]["user_id"]},
    )
    assert request.status_code == 201
    request_id = request.json()["data"]["request_id"]
    accepted = client.post(f"/api/v1/friend-requests/{request_id}/accept", headers=headers(bia))
    assert accepted.status_code == 200

    presence = client.put("/api/v1/me/presence", headers=headers(ana), json={"availability": "online"})
    assert presence.status_code == 200
    friend_list = client.get("/api/v1/friends", headers=headers(bia)).json()["data"]["items"]
    assert friend_list == [
        {
            "user_id": ana["user"]["user_id"],
            "handle": "ana_player",
            "display_name": "Ana_Player",
            "user_type": "account",
            "availability": "online",
        }
    ]

    ticket = client.post("/api/v1/event-tickets", headers=headers(bia)).json()["data"]["ticket"]
    with client.websocket_connect("/api/v1/events/ws") as socket:
        socket.send_json({"type": "auth", "protocol_version": 1, "ticket": ticket, "resume_cursor": 0})
        assert socket.receive_json()["type"] == "authenticated"
        event_types = {socket.receive_json()["type"] for _ in range(3)}
        assert "friend_request.created" in event_types
        assert "friendship.changed" in event_types
        assert "presence.changed" in event_types


def test_party_invite_and_leadership_transfer(client):
    leader = register(client, "party_leader")
    member = register(client, "party_member")
    party = client.post("/api/v1/parties", headers=headers(leader)).json()["data"]
    invite = client.post(
        "/api/v1/invites",
        headers=headers(leader),
        json={
            "target_type": "party",
            "target_id": party["party_id"],
            "recipient_user_id": member["user"]["user_id"],
        },
    ).json()["data"]
    joined = client.post("/api/v1/invites/accept", headers=headers(member), json={"code": invite["code"]})
    assert joined.status_code == 200
    assert len(joined.json()["data"]["target"]["members"]) == 2

    message = client.post(
        f"/api/v1/channels/party/{party['party_id']}/messages",
        headers=headers(member),
        json={"client_message_id": "party-msg-1", "text": "  Olá   grupo!  "},
    )
    assert message.status_code == 201
    assert message.json()["data"]["text"] == "Olá grupo!"
    replay = client.post(
        f"/api/v1/channels/party/{party['party_id']}/messages",
        headers=headers(member),
        json={"client_message_id": "party-msg-1", "text": "não duplica"},
    )
    assert replay.json()["data"]["message_id"] == message.json()["data"]["message_id"]
    history = client.get(f"/api/v1/channels/party/{party['party_id']}/messages", headers=headers(leader)).json()["data"]
    assert [item["text"] for item in history["items"]] == ["Olá grupo!"]

    assert client.post(f"/api/v1/parties/{party['party_id']}/leave", headers=headers(leader)).status_code == 204
    remaining = client.get(f"/api/v1/parties/{party['party_id']}", headers=headers(member)).json()["data"]
    assert remaining["leader_id"] == member["user"]["user_id"]
    assert remaining["revision"] == 3


def test_lobby_code_ready_and_password(client):
    leader = register(client, "lobby_leader")
    member = register(client, "lobby_member")
    lobby_response = client.post(
        "/api/v1/lobbies",
        headers=headers(leader),
        json={
            "name": "Sala Brasil",
            "visibility": "private",
            "password": "segredo-forte",
            "capacity": 4,
            "rounds": 10,
            "map_id": "classic",
            "seed": 1,
            "bots": 1,
        },
    )
    assert lobby_response.status_code == 201
    lobby = lobby_response.json()["data"]
    invite = client.post(
        "/api/v1/invites",
        headers=headers(leader),
        json={"target_type": "lobby", "target_id": lobby["lobby_id"], "max_uses": 2},
    ).json()["data"]
    wrong = client.post(
        "/api/v1/invites/accept", headers=headers(member), json={"code": invite["code"], "password": "incorreta"}
    )
    assert wrong.status_code == 403
    joined = client.post(
        "/api/v1/invites/accept", headers=headers(member), json={"code": invite["code"], "password": "segredo-forte"}
    )
    assert joined.status_code == 200
    current = joined.json()["data"]["target"]
    assert current["revision"] == 2
    ready = client.put(
        f"/api/v1/lobbies/{lobby['lobby_id']}/members/me/ready",
        headers=headers(member),
        json={"revision": current["revision"], "ready": True},
    )
    assert ready.status_code == 200
    assert (
        next(item for item in ready.json()["data"]["members"] if item["user_id"] == member["user"]["user_id"])[
            "ready_revision"
        ]
        == 2
    )


def test_legacy_directory_is_cacheable_and_does_not_leak_managed_rooms(client):
    session = register(client, "directory_host")
    client.post(
        "/api/v1/lobbies",
        headers=headers(session),
        json={
            "name": "Managed private",
            "visibility": "private",
            "password": "password-123",
            "capacity": 4,
            "rounds": 10,
            "map_id": "classic",
            "seed": 1,
        },
    )
    response = client.get("/servers.json")
    assert response.status_code == 200
    assert response.json() == {"schema": 1, "servers": []}
    cached = client.get("/servers.json", headers={"If-None-Match": response.headers["etag"]})
    assert cached.status_code == 304
    assert client.get("/session-token.json?player_name=Guest").status_code == 410


def test_matchmaking_reserves_group_atomically(client):
    leader = register(client, "queue_leader")
    member = register(client, "queue_member")
    host = register(client, "queue_host")
    lobby = client.post(
        "/api/v1/lobbies",
        headers=headers(host),
        json={
            "name": "Queue target",
            "visibility": "public",
            "capacity": 3,
            "rounds": 10,
            "map_id": "classic",
            "seed": 1,
            "bots": 0,
        },
    ).json()["data"]
    party = client.post("/api/v1/parties", headers=headers(leader)).json()["data"]
    invite = client.post(
        "/api/v1/invites",
        headers=headers(leader),
        json={"target_type": "party", "target_id": party["party_id"], "recipient_user_id": member["user"]["user_id"]},
    ).json()["data"]
    client.post("/api/v1/invites/accept", headers=headers(member), json={"code": invite["code"]})
    party = client.get(f"/api/v1/parties/{party['party_id']}", headers=headers(leader)).json()["data"]
    for session in (leader, member):
        response = client.put(
            f"/api/v1/parties/{party['party_id']}/members/me/ready",
            headers=headers(session),
            json={"revision": party["revision"], "ready": True},
        )
        assert response.status_code == 200
    queued = client.post(
        "/api/v1/matchmaking/queue",
        headers=headers(leader),
        json={
            "party_id": party["party_id"],
            "party_revision": party["revision"],
            "criteria": {"target_lobby_id": lobby["lobby_id"]},
        },
    )
    assert queued.status_code == 201, queued.text
    queue = queued.json()["data"]
    assert queue["state"] == "reserved"
    reservation_id = queue["reservation_id"]
    for session in (leader, member):
        accepted = client.post(f"/api/v1/reservations/{reservation_id}/accept", headers=headers(session))
        assert accepted.status_code == 200
    reservation = client.get(f"/api/v1/reservations/{reservation_id}", headers=headers(member)).json()["data"]
    assert reservation["state"] == "preparing"
    assert all(item["accepted"] for item in reservation["members"])
    ticket = client.post(
        f"/api/v1/reservations/{reservation_id}/admission-tickets",
        headers=headers(member),
        json={"transport": "wss"},
    ).json()["data"]
    redeemed = client.post(
        "/internal/v1/admissions/redeem",
        headers={"X-Groundfire-Internal": "local-worker"},
        json={"ticket": ticket["admission_ticket"]},
    )
    assert redeemed.status_code == 200
    replay = client.post(
        "/internal/v1/admissions/redeem",
        headers={"X-Groundfire-Internal": "local-worker"},
        json={"ticket": ticket["admission_ticket"]},
    )
    assert replay.status_code == 409
