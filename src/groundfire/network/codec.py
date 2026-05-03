from __future__ import annotations

import json
from typing import Any

from groundfire_net.codec import JsonDataclassCodec, to_plain

from ..sim.match import MatchSnapshot, ReplicatedPlayerState
from ..sim.world import ReplicatedEntityState, TerrainPatch
from .messages import (
    ClientCommandEnvelope,
    DisconnectNotice,
    HelloAccept,
    HelloRequest,
    JoinAccept,
    JoinReject,
    JoinRequest,
    LanServerAnnouncement,
    Ping,
    Pong,
    ServerEventEnvelope,
    ServerSnapshotEnvelope,
    SessionToken,
)


_CODEC = JsonDataclassCodec(lambda message_type, payload: _decode_typed_message(message_type, payload))


def encode_message(message) -> bytes:
    return _CODEC.encode(message)


def decode_message(payload: bytes):
    return _CODEC.decode(payload)


def encode_json(message) -> str:
    return json.dumps(
        {
            "message_type": type(message).__name__,
            "payload": to_plain(message),
        },
        sort_keys=True,
    )


def decode_json(payload: str):
    decoded = json.loads(payload)
    return _decode_typed_message(decoded["message_type"], decoded["payload"])


def _decode_typed_message(message_type: str, payload: dict[str, Any]):
    if message_type == "SessionToken":
        return SessionToken(**payload)
    if message_type == "HelloRequest":
        return HelloRequest(**payload)
    if message_type == "HelloAccept":
        return HelloAccept(**payload)
    if message_type == "JoinRequest":
        return JoinRequest(**payload)
    if message_type == "JoinAccept":
        return JoinAccept(**payload)
    if message_type == "JoinReject":
        return JoinReject(**payload)
    if message_type == "Ping":
        return Ping(**payload)
    if message_type == "Pong":
        return Pong(**payload)
    if message_type == "DisconnectNotice":
        return DisconnectNotice(**payload)
    if message_type == "ClientCommandEnvelope":
        return ClientCommandEnvelope(
            session_id=payload["session_id"],
            player_number=int(payload["player_number"]),
            client_sequence=int(payload["client_sequence"]),
            acknowledged_snapshot_sequence=payload.get("acknowledged_snapshot_sequence"),
            simulation_tick=int(payload["simulation_tick"]),
            issued_at=float(payload["issued_at"]),
            source=str(payload["source"]),
            commands={str(key): bool(value) for key, value in payload.get("commands", {}).items()},
            session_token=payload.get("session_token"),
            protocol_version=int(payload["protocol_version"]),
        )
    if message_type == "ServerSnapshotEnvelope":
        return ServerSnapshotEnvelope(
            session_id=payload["session_id"],
            snapshot_sequence=int(payload["snapshot_sequence"]),
            simulation_tick=int(payload["simulation_tick"]),
            acknowledged_command_sequences={
                int(key): int(value) for key, value in payload.get("acknowledged_command_sequences", {}).items()
            },
            snapshot=_decode_match_snapshot(payload["snapshot"]),
            removed_entity_ids=tuple(int(item) for item in payload.get("removed_entity_ids", [])),
            removed_player_numbers=tuple(int(item) for item in payload.get("removed_player_numbers", [])),
            terrain_patches=tuple(_decode_terrain_patch(item) for item in payload.get("terrain_patches", [])),
            events=tuple(dict(item) for item in payload.get("events", [])),
            snapshot_kind=str(payload.get("snapshot_kind", "full")),
            baseline_snapshot_sequence=payload.get("baseline_snapshot_sequence"),
            protocol_version=int(payload["protocol_version"]),
        )
    if message_type == "ServerEventEnvelope":
        return ServerEventEnvelope(
            session_id=payload["session_id"],
            event_sequence=int(payload["event_sequence"]),
            simulation_tick=int(payload["simulation_tick"]),
            events=tuple(dict(item) for item in payload.get("events", [])),
            protocol_version=int(payload["protocol_version"]),
        )
    if message_type == "LanServerAnnouncement":
        return LanServerAnnouncement(**payload)
    raise ValueError(f"Unsupported message type: {message_type}")


def _decode_match_snapshot(payload: dict[str, Any]) -> MatchSnapshot:
    return MatchSnapshot(
        authority=str(payload["authority"]),
        game_phase=str(payload["game_phase"]),
        current_round=int(payload["current_round"]),
        num_rounds=int(payload["num_rounds"]),
        simulation_tick=int(payload["simulation_tick"]),
        players=tuple(_decode_player(item) for item in payload.get("players", [])),
        entities=tuple(_decode_entity(item) for item in payload.get("entities", [])),
        phase_ticks_remaining=int(payload.get("phase_ticks_remaining", 0)),
        round_winner_player_number=payload.get("round_winner_player_number"),
        winner_player_number=payload.get("winner_player_number"),
        seed=int(payload.get("seed", 0)),
        world_width=float(payload.get("world_width", 11.0)),
        terrain_revision=int(payload.get("terrain_revision", 0)),
        terrain_profile=tuple(float(height) for height in payload.get("terrain_profile", [])),
    )


def _decode_player(payload: dict[str, Any]) -> ReplicatedPlayerState:
    raw_colour = payload.get("colour", (255, 255, 255))
    return ReplicatedPlayerState(
        player_number=int(payload["player_number"]),
        name=str(payload["name"]),
        score=int(payload.get("score", 0)),
        money=int(payload.get("money", 0)),
        connected=bool(payload.get("connected", True)),
        is_computer=bool(payload.get("is_computer", False)),
        tank_entity_id=payload.get("tank_entity_id"),
        acknowledged_command_sequence=int(payload.get("acknowledged_command_sequence", 0)),
        acknowledged_snapshot_sequence=int(payload.get("acknowledged_snapshot_sequence", 0)),
        colour=(int(raw_colour[0]), int(raw_colour[1]), int(raw_colour[2])),
        is_leader=bool(payload.get("is_leader", False)),
        selected_weapon=str(payload.get("selected_weapon", "shell")),
        weapon_stocks=tuple(
            (str(item[0]), int(item[1]))
            for item in payload.get("weapon_stocks", ())
        ),
        round_defeated_player_numbers=tuple(
            int(player_number)
            for player_number in payload.get("round_defeated_player_numbers", ())
        ),
    )


def _decode_entity(payload: dict[str, Any]) -> ReplicatedEntityState:
    position = payload.get("position", (0.0, 0.0))
    velocity = payload.get("velocity", (0.0, 0.0))
    return ReplicatedEntityState(
        entity_id=int(payload["entity_id"]),
        entity_type=str(payload["entity_type"]),
        position=(float(position[0]), float(position[1])),
        velocity=(float(velocity[0]), float(velocity[1])),
        angle=float(payload.get("angle", 0.0)),
        owner_player=payload.get("owner_player"),
        payload=dict(payload.get("payload", {})),
    )


def _decode_terrain_patch(payload: dict[str, Any]) -> TerrainPatch:
    return TerrainPatch(
        patch_id=int(payload["patch_id"]),
        chunk_index=int(payload["chunk_index"]),
        operation=str(payload["operation"]),
        payload=dict(payload.get("payload", {})),
    )
