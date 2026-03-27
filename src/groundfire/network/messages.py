from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..sim.match import MatchSnapshot
from ..sim.world import TerrainPatch

PROTOCOL_VERSION = 1
DEFAULT_GAME_PORT = 27015
DEFAULT_DISCOVERY_PORT = 27016
SIMULATION_HZ = 60
SNAPSHOT_HZ = 20


@dataclass(frozen=True)
class SessionToken:
    token: str
    player_number: int


@dataclass(frozen=True)
class HelloRequest:
    player_name: str = "Player"
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class HelloAccept:
    session_id: str
    server_name: str
    current_round: int
    player_count: int
    max_players: int
    simulation_hz: int = SIMULATION_HZ
    snapshot_hz: int = SNAPSHOT_HZ
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class JoinRequest:
    player_name: str
    requested_slot: int | None = None
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class JoinAccept:
    session_id: str
    player_number: int
    session_token: str
    simulation_hz: int = SIMULATION_HZ
    snapshot_hz: int = SNAPSHOT_HZ
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class JoinReject:
    reason: str
    session_id: str | None = None
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class Ping:
    nonce: str
    issued_at: float
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class Pong:
    nonce: str
    issued_at: float
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class DisconnectNotice:
    session_id: str
    player_number: int
    session_token: str
    reason: str = ""
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class ClientCommandEnvelope:
    session_id: str
    player_number: int
    client_sequence: int
    acknowledged_snapshot_sequence: int | None
    simulation_tick: int
    issued_at: float
    source: str
    commands: dict[str, bool] = field(default_factory=dict)
    session_token: str | None = None
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class ServerSnapshotEnvelope:
    session_id: str
    snapshot_sequence: int
    simulation_tick: int
    acknowledged_command_sequences: dict[int, int]
    snapshot: MatchSnapshot
    removed_entity_ids: tuple[int, ...] = field(default_factory=tuple)
    removed_player_numbers: tuple[int, ...] = field(default_factory=tuple)
    terrain_patches: tuple[TerrainPatch, ...] = field(default_factory=tuple)
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    snapshot_kind: str = "full"
    baseline_snapshot_sequence: int | None = None
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class ServerEventEnvelope:
    session_id: str
    event_sequence: int
    simulation_tick: int
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    protocol_version: int = PROTOCOL_VERSION


@dataclass(frozen=True)
class LanServerAnnouncement:
    server_name: str
    session_id: str
    map_seed: int
    current_round: int
    player_count: int
    max_players: int
    requires_password: bool
    server_port: int
    protocol_version: int = PROTOCOL_VERSION
