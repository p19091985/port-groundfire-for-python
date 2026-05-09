from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import os
import struct
import time
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any

from groundfire_net.codec import to_plain
from src.groundfire.sim.match import MatchState, ReplicatedPlayerState
from src.groundfire.sim.world import WorldState

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
PROTOCOL_VERSION = 1
MIN_PROTOCOL_VERSION = 1
MAX_PROTOCOL_VERSION = PROTOCOL_VERSION
SUPPORTED_PROTOCOL_VERSIONS = tuple(range(MIN_PROTOCOL_VERSION, MAX_PROTOCOL_VERSION + 1))
MATCH_SNAPSHOT_SCHEMA_VERSION = 1
EVENT_SCHEMA_VERSION = 1
INPUT_COMMAND_FIELDS = frozenset(
    {
        "aim_left",
        "aim_right",
        "power_up",
        "power_down",
        "move_left",
        "move_right",
        "jump",
        "fire",
        "weapon_next",
        "weapon_prev",
    }
)


@dataclass
class GatewayJoinRegistry:
    max_players: int = 0
    active_players: int = 0

    def acquire_slot(self) -> bool:
        if self.max_players > 0 and self.active_players >= self.max_players:
            return False
        self.active_players += 1
        return True

    def release_slot(self) -> None:
        self.active_players = max(0, self.active_players - 1)

    def metadata(self) -> dict[str, int]:
        return {"max_players": self.max_players, "players_connected": self.active_players}


@dataclass
class GatewaySimulation:
    session_id: str = "web-dev"
    world: WorldState = field(default_factory=lambda: WorldState(seed=1401))
    match: MatchState = field(default_factory=lambda: MatchState(session_id="web-dev", game_phase="lobby"))
    player_number: int = 1
    player_name: str = "Guest"
    last_input: dict[str, Any] = field(default_factory=dict)
    sequence: int = 0
    tank_entity_id: int | None = None
    projectile_entity_id: int | None = None

    def join(self, player_name: str) -> None:
        self.player_name = player_name
        if self.tank_entity_id is None:
            tank = self.world.entity_registry.create(
                "tank",
                position=(-6.0, self.world.terrain.height_at(-6.0)),
                owner_player=self.player_number,
                payload={"health": 100, "fuel": 1.0, "weapon": "shell"},
            )
            self.tank_entity_id = tank.entity_id
        self.match.upsert_player(
            ReplicatedPlayerState(
                player_number=self.player_number,
                name=self.player_name,
                connected=True,
                tank_entity_id=self.tank_entity_id,
                is_leader=True,
                selected_weapon="shell",
                weapon_stocks=(("shell", -1), ("machine_gun", 50), ("missile", 4), ("mirv", 3), ("nuke", 1)),
            )
        )
        self.match.game_phase = "online"

    def apply_input(self, sequence: int, command: dict[str, Any]) -> None:
        self.sequence = sequence
        self.last_input = dict(command)
        self.match.simulation_tick += 1
        tank = self.world.entity_registry.get(self.tank_entity_id or -1)
        if tank is None:
            return
        x, _y = tank.position
        angle = tank.angle
        if command.get("move_left"):
            x -= 0.08
        if command.get("move_right"):
            x += 0.08
        if command.get("aim_left"):
            angle += 1.5
        if command.get("aim_right"):
            angle -= 1.5
        x = max(-(self.world.width / 2.0), min(self.world.width / 2.0, x))
        y = self.world.terrain.height_at(x)
        payload = dict(tank.payload)
        payload["last_input"] = dict(command)
        if command.get("fire"):
            projectile = self.world.entity_registry.create(
                "projectile",
                position=(round(x + 1.0, 4), round(y + 0.6, 4)),
                velocity=(1.8, 1.2),
                angle=angle,
                owner_player=self.player_number,
                payload={"weapon": "shell", "ttl": 0.45},
            )
            self.projectile_entity_id = projectile.entity_id
            patch = self.world.apply_explosion(x + 1.0, y, 0.55, caused_by=self.player_number)
            if patch is not None:
                self.match.queue_event(
                    "terrain_explosion",
                    patch_id=patch.patch_id,
                    position=(round(x + 1.0, 4), round(y, 4)),
                    radius=0.55,
                )
        elif self.projectile_entity_id is not None:
            projectile = self.world.entity_registry.get(self.projectile_entity_id)
            if projectile is not None:
                px, py = projectile.position
                vx, vy = projectile.velocity
                ttl = float(projectile.payload.get("ttl", 0.0)) - 0.08
                if ttl <= 0.0:
                    self.world.entity_registry.remove(self.projectile_entity_id)
                    self.projectile_entity_id = None
                else:
                    payload = dict(projectile.payload)
                    payload["ttl"] = round(ttl, 4)
                    self.world.entity_registry.replace(
                        replace(
                            projectile,
                            position=(round(px + vx * 0.08, 4), round(py + vy * 0.08, 4)),
                            payload=payload,
                        )
                    )
        updated = replace(tank, position=(round(x, 4), round(y, 4)), angle=round(angle, 4), payload=payload)
        self.world.entity_registry.replace(updated)
        self.match.update_player(self.player_number, acknowledged_command_sequence=sequence)

    def snapshot(self, *, status: str) -> dict[str, Any]:
        snapshot = self.match.snapshot(
            self.world.snapshot_entities(),
            seed=self.world.seed,
            world_width=self.world.width,
            terrain_revision=self.world.terrain_revision,
            terrain_profile=self.world.snapshot_terrain_profile(),
        )
        return {
            "type": "snapshot",
            "protocol": PROTOCOL_VERSION,
            "sequence": self.sequence,
            "state": {
                "status": status,
                "player_name": self.player_name,
                "joined": self.tank_entity_id is not None,
                "last_input": self.last_input,
                "server_time_msec": int(time.time() * 1000),
                "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
                "event_schema": EVENT_SCHEMA_VERSION,
                "match_snapshot": to_plain(snapshot),
                "terrain_patches": [to_plain(patch) for patch in self.world.drain_terrain_patches()],
                "events": [_version_event(event) for event in self.match.drain_events()],
            },
        }


@dataclass
class WebSocketGatewaySession:
    simulation: GatewaySimulation = field(default_factory=GatewaySimulation)
    required_password: str = ""
    required_auth_token: str = ""
    join_registry: GatewayJoinRegistry = field(default_factory=GatewayJoinRegistry)
    joins_closed: bool = False
    banned_players: frozenset[str] = field(default_factory=frozenset)
    _joined: bool = False

    def handle_text(self, payload: str) -> list[dict[str, Any]]:
        try:
            message = json.loads(payload)
        except json.JSONDecodeError:
            return [_error("invalid_json")]
        if not isinstance(message, dict):
            return [_error("invalid_message")]
        protocol_error = _validate_protocol(message)
        if protocol_error is not None:
            return [protocol_error]

        message_type = str(message.get("type", ""))
        shape_error = _validate_message_shape(message_type, message)
        if shape_error is not None:
            return [shape_error]

        if message_type == "hello":
            return [
                {
                    "type": "hello",
                    "protocol": PROTOCOL_VERSION,
                    "min_protocol": MIN_PROTOCOL_VERSION,
                    "max_protocol": MAX_PROTOCOL_VERSION,
                    "supported_protocols": list(SUPPORTED_PROTOCOL_VERSIONS),
                    "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
                    "event_schema": EVENT_SCHEMA_VERSION,
                    "password_required": bool(self.required_password),
                    "auth_required": bool(self.required_auth_token),
                    "joins_open": not self.joins_closed,
                    "ban_enforced": bool(self.banned_players),
                    **self.join_registry.metadata(),
                    "server": "python-websocket-gateway",
                }
            ]
        if message_type == "join":
            if self.joins_closed:
                return [_error("server_closed")]
            player_name = str(message.get("player_name", self.simulation.player_name))
            if _normalized_player_name(player_name) in self.banned_players:
                return [_error("banned")]
            if self.required_auth_token and str(message.get("auth_token", "")) != self.required_auth_token:
                return [_error("authentication_failed")]
            if self.required_password and str(message.get("password", "")) != self.required_password:
                return [_error("invalid_password")]
            if not self._joined:
                if not self.join_registry.acquire_slot():
                    return [_error("server_full", **self.join_registry.metadata())]
                self._joined = True
            self.simulation.join(player_name)
            return [self.simulation.snapshot(status="joined")]
        if message_type == "input":
            sequence = int(message.get("sequence", self.simulation.sequence + 1))
            command = message.get("command", {})
            self.simulation.apply_input(sequence, command if isinstance(command, dict) else {})
            return [self.simulation.snapshot(status="input")]
        if message_type == "ping":
            return [
                {
                    "type": "pong",
                    "protocol": PROTOCOL_VERSION,
                    "sequence": int(message.get("sequence", 0)),
                    "client_time_msec": int(message.get("client_time_msec", 0)),
                    "server_time_msec": int(time.time() * 1000),
                }
            ]
        if message_type == "disconnect":
            self.close()
            return [
                {
                    "type": "disconnect",
                    "protocol": PROTOCOL_VERSION,
                    "reason": str(message.get("reason", "client_disconnect")),
                }
            ]
        return [_error("unknown_type", received_type=message_type)]

    def close(self) -> None:
        if not self._joined:
            return
        self.join_registry.release_slot()
        self._joined = False


class WebSocketGateway:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27080,
        *,
        password: str = "",
        auth_token: str = "",
        max_players: int = 0,
        closed: bool = False,
        banned_players: Iterable[str] = (),
    ):
        self.host = host
        self.port = port
        self.password = password
        self.auth_token = auth_token
        self.closed = closed
        self.banned_players = _normalized_player_names(banned_players)
        self.join_registry = GatewayJoinRegistry(max_players=max(0, max_players))

    async def serve_forever(self) -> None:
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        session = WebSocketGatewaySession(
            required_password=self.password,
            required_auth_token=self.auth_token,
            join_registry=self.join_registry,
            joins_closed=self.closed,
            banned_players=self.banned_players,
        )
        try:
            await _accept_handshake(reader, writer)
            connected_snapshot = session.simulation.snapshot(status="connected")
            await _write_text(writer, json.dumps(connected_snapshot, separators=(",", ":")))
            while not reader.at_eof():
                payload = await _read_frame(reader)
                if payload is None:
                    break
                for response in session.handle_text(payload):
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))
                    if response.get("type") == "disconnect":
                        return
        finally:
            session.close()
            writer.close()
            await writer.wait_closed()


async def _accept_handshake(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    request = await reader.readuntil(b"\r\n\r\n")
    headers = _parse_headers(request.decode("utf-8", errors="replace"))
    key = headers.get("sec-websocket-key")
    if not key:
        raise ValueError("missing Sec-WebSocket-Key")
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
    writer.write(
        (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n"
            "\r\n"
        ).encode("ascii")
    )
    await writer.drain()


def _parse_headers(request: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in request.splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    return headers


async def _read_frame(reader: asyncio.StreamReader) -> str | None:
    header = await reader.readexactly(2)
    first, second = header
    opcode = first & 0x0F
    if opcode == 0x8:
        return None
    if opcode != 0x1:
        raise ValueError(f"unsupported websocket opcode: {opcode}")
    masked = bool(second & 0x80)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    mask = await reader.readexactly(4) if masked else b""
    payload = bytearray(await reader.readexactly(length))
    if masked:
        for index in range(length):
            payload[index] ^= mask[index % 4]
    return payload.decode("utf-8")


async def _write_text(writer: asyncio.StreamWriter, payload: str) -> None:
    data = payload.encode("utf-8")
    header = bytearray([0x81])
    if len(data) < 126:
        header.append(len(data))
    elif len(data) < 65536:
        header.append(126)
        header.extend(struct.pack("!H", len(data)))
    else:
        header.append(127)
        header.extend(struct.pack("!Q", len(data)))
    writer.write(bytes(header) + data)
    await writer.drain()


def _error(message: str, **extra: Any) -> dict[str, Any]:
    payload = {"type": "error", "protocol": PROTOCOL_VERSION, "message": message}
    payload.update(extra)
    return payload


def _validate_protocol(message: dict[str, Any]) -> dict[str, Any] | None:
    if "protocol" not in message:
        return _protocol_error("missing_protocol")
    raw_protocol = message["protocol"]
    if not isinstance(raw_protocol, int) or isinstance(raw_protocol, bool):
        return _protocol_error("invalid_protocol", received_protocol=raw_protocol)
    if raw_protocol not in SUPPORTED_PROTOCOL_VERSIONS:
        return _protocol_error("protocol_mismatch", received_protocol=raw_protocol)
    return None


def _protocol_error(message: str, **extra: Any) -> dict[str, Any]:
    return _error(
        message,
        expected_protocol=PROTOCOL_VERSION,
        min_protocol=MIN_PROTOCOL_VERSION,
        max_protocol=MAX_PROTOCOL_VERSION,
        supported_protocols=list(SUPPORTED_PROTOCOL_VERSIONS),
        **extra,
    )


def _validate_message_shape(message_type: str, message: dict[str, Any]) -> dict[str, Any] | None:
    if message_type == "hello":
        return _optional_string_field(message, "client")
    if message_type == "join":
        return (
            _required_string_field(message, "player_name")
            or _optional_string_field(message, "password")
            or _optional_string_field(message, "auth_token")
        )
    if message_type == "input":
        shape_error = _required_integer_field(message, "sequence") or _required_dict_field(message, "command")
        if shape_error is not None:
            return shape_error
        return _validate_input_command(message["command"])
    if message_type == "ping":
        return _required_integer_field(message, "sequence") or _required_integer_field(message, "client_time_msec")
    if message_type == "disconnect":
        return _optional_string_field(message, "reason")
    return None


def _required_string_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name not in message:
        return _error("missing_field", field=field_name)
    return _optional_string_field(message, field_name)


def _optional_string_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name in message and not isinstance(message[field_name], str):
        return _error("invalid_field", field=field_name, expected="string")
    return None


def _required_integer_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name not in message:
        return _error("missing_field", field=field_name)
    if not isinstance(message[field_name], int) or isinstance(message[field_name], bool):
        return _error("invalid_field", field=field_name, expected="integer")
    return None


def _required_dict_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name not in message:
        return _error("missing_field", field=field_name)
    if not isinstance(message[field_name], dict):
        return _error("invalid_field", field=field_name, expected="object")
    return None


def _validate_input_command(command: dict[str, Any]) -> dict[str, Any] | None:
    for field_name, value in command.items():
        if field_name not in INPUT_COMMAND_FIELDS:
            return _error("unknown_command", command=field_name)
        if not isinstance(value, bool):
            return _error("invalid_command", command=field_name, expected="boolean")
    return None


def _version_event(event: dict[str, Any]) -> dict[str, Any]:
    versioned = dict(event)
    versioned.setdefault("schema", EVENT_SCHEMA_VERSION)
    return versioned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Groundfire browser-safe WebSocket gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=27080)
    parser.add_argument(
        "--password",
        default=os.environ.get("GROUNDFIRE_WEB_GATEWAY_PASSWORD", ""),
        help="Optional join password. Also configurable through GROUNDFIRE_WEB_GATEWAY_PASSWORD.",
    )
    parser.add_argument(
        "--auth-token",
        default=os.environ.get("GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN", ""),
        help="Optional join auth token. Also configurable through GROUNDFIRE_WEB_GATEWAY_AUTH_TOKEN.",
    )
    parser.add_argument(
        "--max-players",
        type=_non_negative_int,
        default=_environment_int("GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS", 0),
        help=(
            "Optional active player limit. Use 0 for no limit. "
            "Also configurable through GROUNDFIRE_WEB_GATEWAY_MAX_PLAYERS."
        ),
    )
    parser.add_argument(
        "--closed",
        action="store_true",
        default=_environment_bool("GROUNDFIRE_WEB_GATEWAY_CLOSED", False),
        help="Reject new joins with server_closed. Also configurable through GROUNDFIRE_WEB_GATEWAY_CLOSED.",
    )
    parser.add_argument(
        "--ban-player",
        action="append",
        default=_environment_list("GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS"),
        metavar="NAME",
        help=(
            "Reject joins from this player name with banned. May be repeated. "
            "Also configurable through comma-separated GROUNDFIRE_WEB_GATEWAY_BANNED_PLAYERS."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    gateway = WebSocketGateway(
        args.host,
        args.port,
        password=args.password,
        auth_token=args.auth_token,
        max_players=args.max_players,
        closed=args.closed,
        banned_players=args.ban_player,
    )
    asyncio.run(gateway.serve_forever())
    return 0


def _environment_list(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def _environment_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "closed"}


def _environment_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def _normalized_player_names(values: Iterable[str]) -> frozenset[str]:
    names: set[str] = set()
    for value in values:
        for item in str(value).split(","):
            normalized = _normalized_player_name(item)
            if normalized:
                names.add(normalized)
    return frozenset(names)


def _normalized_player_name(value: str) -> str:
    return value.strip().casefold()


if __name__ == "__main__":
    raise SystemExit(main())
