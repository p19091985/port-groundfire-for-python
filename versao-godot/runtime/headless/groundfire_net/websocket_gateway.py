from __future__ import annotations

import argparse
import asyncio
import base64
import contextlib
import hashlib
import hmac
import json
import os
import struct
import time
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from groundfire_net.codec import to_plain

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
PROTOCOL_VERSION = 2
MIN_PROTOCOL_VERSION = 1
MAX_PROTOCOL_VERSION = PROTOCOL_VERSION
SUPPORTED_PROTOCOL_VERSIONS = tuple(range(MIN_PROTOCOL_VERSION, MAX_PROTOCOL_VERSION + 1))
MATCH_SNAPSHOT_SCHEMA_VERSION = 1
EVENT_SCHEMA_VERSION = 1
MATCH_SNAPSHOT_SCHEMA_REQUIRED_FIELDS = frozenset(
    {
        "authority",
        "game_phase",
        "current_round",
        "num_rounds",
        "simulation_tick",
        "players",
        "entities",
        "phase_ticks_remaining",
        "round_winner_player_number",
        "winner_player_number",
        "seed",
        "world_width",
        "terrain_revision",
        "terrain_profile",
    }
)
REPLICATED_PLAYER_SCHEMA_REQUIRED_FIELDS = frozenset(
    {
        "player_number",
        "name",
        "score",
        "money",
        "connected",
        "is_computer",
        "tank_entity_id",
        "acknowledged_command_sequence",
        "acknowledged_snapshot_sequence",
        "colour",
        "is_leader",
        "is_ready",
        "rematch_ready",
        "selected_weapon",
        "weapon_stocks",
        "round_defeated_player_numbers",
    }
)
REPLICATED_ENTITY_SCHEMA_REQUIRED_FIELDS = frozenset(
    {
        "entity_id",
        "entity_type",
        "position",
        "velocity",
        "angle",
        "owner_player",
        "payload",
    }
)
TERRAIN_PATCH_SCHEMA_REQUIRED_FIELDS = frozenset({"patch_id", "chunk_index", "operation", "payload"})
EVENT_SCHEMA_REQUIRED_FIELDS = frozenset({"schema", "event_type", "payload"})
SESSION_TOKEN_VERSION = "gf1"
DEFAULT_SESSION_TOKEN_TTL_SECONDS = 3600
INPUT_COMMAND_FIELDS = frozenset(
    {
        "aim_left",
        "aim_right",
        "power_up",
        "power_down",
        "move_left",
        "move_right",
        "jump",
        "shield",
        "fire",
        "weapon_next",
        "weapon_prev",
        "ready",
        "rematch",
    }
)


@dataclass
class GatewayJoinRegistry:
    max_players: int = 0
    active_players: int = 0
    _occupied_player_numbers: set[int] = field(default_factory=set)

    def acquire_slot(self) -> bool:
        return self.acquire_player_number() > 0

    def acquire_player_number(self) -> int:
        if self.max_players > 0 and len(self._occupied_player_numbers) >= self.max_players:
            return 0
        player_number = 1
        while player_number in self._occupied_player_numbers:
            player_number += 1
        if self.max_players > 0 and player_number > self.max_players:
            return 0
        self._occupied_player_numbers.add(player_number)
        self._sync_active_players()
        return player_number

    def reserve_player_number(self, player_number: int) -> bool:
        if player_number < 0:
            return False
        if player_number in self._occupied_player_numbers:
            return True
        if self.max_players > 0 and len(self._occupied_player_numbers) >= self.max_players:
            return False
        self._occupied_player_numbers.add(player_number)
        self._sync_active_players()
        return True

    def release_slot(self, player_number: int | None = None) -> None:
        if player_number is None:
            if self._occupied_player_numbers:
                player_number = max(self._occupied_player_numbers)
            else:
                self.active_players = max(0, self.active_players - 1)
                return
        self._occupied_player_numbers.discard(player_number)
        self._sync_active_players()

    def metadata(self) -> dict[str, int]:
        return {"max_players": self.max_players, "players_connected": self.active_players}

    def _sync_active_players(self) -> None:
        self.active_players = len(self._occupied_player_numbers)


@dataclass
class WebSocketGatewaySession:
    required_password: str = ""
    required_auth_token: str = ""
    session_secret: str = ""
    join_registry: GatewayJoinRegistry = field(default_factory=GatewayJoinRegistry)
    joins_closed: bool = False
    banned_players: frozenset[str] = field(default_factory=frozenset)
    _joined: bool = False
    _player_number: int = -1
    _role: str = "player"
    player_name: str = "Guest"
    last_input: dict = field(default_factory=dict)
    last_input_sequence: int = 0
    acknowledged_snapshot_sequence: int | None = None
    server_session_id: str = ""
    server_session_token: str = ""
    protocol_version: int = PROTOCOL_VERSION

    def hello_response(self, *, server_name: str = "python-websocket-proxy") -> dict[str, Any]:
        return {
            "type": "hello",
            "protocol": self.protocol_version,
            "min_protocol": MIN_PROTOCOL_VERSION,
            "max_protocol": MAX_PROTOCOL_VERSION,
            "supported_protocols": list(SUPPORTED_PROTOCOL_VERSIONS),
            "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
            "event_schema": EVENT_SCHEMA_VERSION,
            "capabilities": [
                "lobby_ready",
                "match_rematch",
                "session_resume",
                "chat",
                "spectator",
            ]
            if self.protocol_version >= 2
            else [],
            "password_required": bool(self.required_password),
            "auth_required": bool(self.required_auth_token or self.session_secret),
            "auth_token_mode": _auth_token_mode(self.required_auth_token, self.session_secret),
            "joins_open": not self.joins_closed,
            "ban_enforced": bool(self.banned_players),
            **self.join_registry.metadata(),
            "server": server_name,
        }

    def prepare_join(self, message: dict[str, Any]) -> dict[str, Any] | None:
        if self.joins_closed:
            return _error("server_closed")
        player_name = str(message.get("player_name", "Guest"))
        if _normalized_player_name(player_name) in self.banned_players:
            return _error("banned")
        if not _auth_token_is_authorized(
            str(message.get("auth_token", "")),
            required_auth_token=self.required_auth_token,
            session_secret=self.session_secret,
            player_name=player_name,
        ):
            return _error("authentication_failed")
        if self.required_password and str(message.get("password", "")) != self.required_password:
            return _error("invalid_password")
        self._role = "spectator" if bool(message.get("spectator", False)) else "player"
        if self._role == "player" and not self._joined and self._player_number < 0:
            player_number = self.join_registry.acquire_player_number()
            if player_number <= 0:
                return _error("server_full", **self.join_registry.metadata())
            self._player_number = player_number
        self.player_name = player_name
        return None

    def confirm_join(
        self,
        player_number: int,
        *,
        session_id: str,
        session_token: str,
        role: str = "player",
    ) -> None:
        self._role = role
        if role == "spectator":
            if self._player_number >= 0:
                self.join_registry.release_slot(self._player_number)
            self._player_number = -1
            self.server_session_id = session_id
            self.server_session_token = session_token
            self._joined = True
            return
        if self._player_number != player_number:
            if self._player_number >= 0:
                self.join_registry.release_slot(self._player_number)
            if not self.join_registry.reserve_player_number(player_number):
                self.join_registry.acquire_slot()
        self._player_number = player_number
        self.server_session_id = session_id
        self.server_session_token = session_token
        self._joined = True

    def reject_join(self) -> None:
        if self._joined or self._player_number < 0:
            return
        self.join_registry.release_slot(self._player_number)
        self._player_number = -1

    def record_input(self, sequence: int, command: dict[str, Any]) -> None:
        self.last_input_sequence = sequence
        self.last_input = dict(command)

    def disconnect_notice(self, reason: str):
        if not self._joined or not self.server_session_token:
            return None
        try:
            from groundfire.network.messages import DisconnectNotice
        except ModuleNotFoundError:
            from src.groundfire.network.messages import DisconnectNotice

        return DisconnectNotice(
            session_id=self.server_session_id or "web",
            player_number=self._player_number,
            session_token=self.server_session_token,
            reason=reason,
        )

    def close(self) -> None:
        if not self._joined:
            return
        if self._role == "player" and self._player_number >= 0:
            self.join_registry.release_slot(self._player_number)
        self._player_number = -1
        self._joined = False


class WebSocketGateway:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 27080,
        *,
        password: str = "",
        auth_token: str = "",
        session_secret: str = "",
        max_players: int = 0,
        closed: bool = False,
        banned_players: Iterable[str] = (),
        udp_host: str = "127.0.0.1",
        udp_port: int = 27015,
        admission_redeem_url: str = "",
        admission_secret: str = "",
    ):
        self.host = host
        self.port = port
        self.password = password
        self.auth_token = auth_token
        self.session_secret = session_secret
        self.closed = closed
        self.udp_host = udp_host
        self.udp_port = udp_port
        self.admission_redeem_url = admission_redeem_url
        self.admission_secret = admission_secret
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
            session_secret=self.session_secret,
            join_registry=self.join_registry,
            joins_closed=self.closed,
            banned_players=self.banned_players,
        )
        ws_queue: asyncio.Queue[object] = asyncio.Queue()

        class UdpProxyProtocol(asyncio.DatagramProtocol):
            def datagram_received(self, data: bytes, addr) -> None:
                try:
                    from groundfire.network.codec import decode_message
                except ModuleNotFoundError:
                    from src.groundfire.network.codec import decode_message

                try:
                    msg = decode_message(data)
                    ws_queue.put_nowait(msg)
                except Exception:
                    pass

        loop = asyncio.get_running_loop()
        transport, _protocol = await loop.create_datagram_endpoint(
            lambda: UdpProxyProtocol(), remote_addr=(self.udp_host, self.udp_port)
        )

        async def udp_to_ws_loop() -> None:
            try:
                from groundfire.network.messages import (
                    CommandResult,
                    HelloAccept,
                    JoinAccept,
                    JoinReject,
                    ResumeAccept,
                    ResumeReject,
                    ServerEventEnvelope,
                    ServerSnapshotEnvelope,
                )
            except ModuleNotFoundError:
                from src.groundfire.network.messages import (
                    CommandResult,
                    HelloAccept,
                    JoinAccept,
                    JoinReject,
                    ResumeAccept,
                    ResumeReject,
                    ServerEventEnvelope,
                    ServerSnapshotEnvelope,
                )

            while True:
                msg = await ws_queue.get()
                if isinstance(msg, HelloAccept):
                    continue
                if isinstance(msg, ServerSnapshotEnvelope):
                    session.acknowledged_snapshot_sequence = msg.snapshot_sequence
                    state = _snapshot_state_for_session(session, msg)
                    response = {
                        "type": "snapshot",
                        "protocol": session.protocol_version,
                        "sequence": session.last_input_sequence,
                        "state": state,
                    }
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))
                elif isinstance(msg, JoinAccept):
                    session.confirm_join(
                        msg.player_number,
                        session_id=msg.session_id,
                        session_token=msg.session_token,
                        role=msg.role,
                    )
                elif isinstance(msg, JoinReject):
                    session.reject_join()
                    reason = "server_full" if msg.reason == "server_full_or_slot_unavailable" else msg.reason
                    await _write_text(
                        writer,
                        json.dumps(_error(reason, protocol=session.protocol_version), separators=(",", ":")),
                    )
                    writer.close()
                elif isinstance(msg, ResumeAccept):
                    session.confirm_join(
                        msg.player_number,
                        session_id=msg.session_id,
                        session_token=msg.session_token,
                    )
                    await _write_text(
                        writer,
                        json.dumps(
                            {
                                "type": "session_resumed",
                                "protocol": session.protocol_version,
                                "session_id": msg.session_id,
                                "player_number": msg.player_number,
                                "resume_token": msg.session_token,
                            },
                            separators=(",", ":"),
                        ),
                    )
                elif isinstance(msg, ResumeReject):
                    await _write_text(
                        writer,
                        json.dumps(
                            _error(msg.reason, protocol=session.protocol_version),
                            separators=(",", ":"),
                        ),
                    )
                elif isinstance(msg, CommandResult):
                    await _write_text(
                        writer,
                        json.dumps(
                            {
                                "type": "command_result",
                                "protocol": session.protocol_version,
                                "request_id": msg.request_id,
                                "command": msg.command,
                                "accepted": msg.accepted,
                                "reason": msg.reason,
                            },
                            separators=(",", ":"),
                        ),
                    )
                elif isinstance(msg, ServerEventEnvelope):
                    for event in msg.events:
                        if str(event.get("event_type", "")) != "chat_message":
                            continue
                        await _write_text(
                            writer,
                            json.dumps(
                                {
                                    "type": "chat_event",
                                    "protocol": session.protocol_version,
                                    "event_sequence": msg.event_sequence,
                                    **dict(event.get("payload", {})),
                                },
                                separators=(",", ":"),
                            ),
                        )

        udp_task = asyncio.create_task(udp_to_ws_loop())
        graceful_disconnect = False

        try:
            await _accept_handshake(reader, writer)

            try:
                from groundfire.network.codec import encode_message
                from groundfire.network.messages import (
                    ChatSendRequest,
                    ClientCommandEnvelope,
                    HelloRequest,
                    JoinRequest,
                    LobbySetReadyRequest,
                    MatchRematchRequest,
                    ResumeRequest,
                )
            except ModuleNotFoundError:
                from src.groundfire.network.codec import encode_message
                from src.groundfire.network.messages import (
                    ChatSendRequest,
                    ClientCommandEnvelope,
                    HelloRequest,
                    JoinRequest,
                    LobbySetReadyRequest,
                    MatchRematchRequest,
                    ResumeRequest,
                )

            while not reader.at_eof():
                payload = await _read_frame(reader)
                if payload is None:
                    break

                try:
                    message = json.loads(payload)
                except json.JSONDecodeError:
                    await _write_text(writer, json.dumps(_error("invalid_json"), separators=(",", ":")))
                    continue
                if not isinstance(message, dict):
                    await _write_text(writer, json.dumps(_error("invalid_message"), separators=(",", ":")))
                    continue
                protocol_error = _validate_protocol(message)
                if protocol_error is not None:
                    await _write_text(writer, json.dumps(protocol_error, separators=(",", ":")))
                    continue
                message_type = str(message.get("type", ""))
                if message_type == "hello":
                    session.protocol_version = int(message.get("protocol", PROTOCOL_VERSION))
                shape_error = _validate_message_shape(message_type, message)
                if shape_error is not None:
                    await _write_text(writer, json.dumps(shape_error, separators=(",", ":")))
                    continue

                if message_type == "hello":
                    transport.sendto(encode_message(HelloRequest(player_name=session.player_name)))
                    await _write_text(
                        writer,
                        json.dumps(session.hello_response(server_name="python-websocket-proxy"), separators=(",", ":")),
                    )

                elif message_type == "join":
                    join_error = session.prepare_join(message)
                    if join_error is not None:
                        join_error["protocol"] = session.protocol_version
                        await _write_text(writer, json.dumps(join_error, separators=(",", ":")))
                        continue
                    if self.admission_redeem_url and not await asyncio.to_thread(
                        _redeem_admission_ticket,
                        self.admission_redeem_url,
                        self.admission_secret,
                        str(message.get("auth_token", "")),
                    ):
                        session.reject_join()
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("authentication_failed", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    transport.sendto(
                        encode_message(
                            JoinRequest(
                                player_name=session.player_name,
                                requested_slot=None,
                                password=str(message.get("password", "")),
                                spectator=bool(message.get("spectator", False)),
                                is_computer=bool(message.get("is_computer", False)),
                            )
                        )
                    )

                elif message_type == "session_resume":
                    if session.protocol_version < 2:
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("unsupported_capability", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    session.player_name = str(message.get("player_name", session.player_name))
                    transport.sendto(
                        encode_message(
                            ResumeRequest(
                                session_id=str(message["session_id"]),
                                player_number=int(message["player_number"]),
                                session_token=str(message["resume_token"]),
                                player_name=session.player_name,
                            )
                        )
                    )

                elif message_type == "input":
                    if not session._joined:
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("not_joined", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    if session._role == "spectator":
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("spectator_read_only", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    sequence = int(message["sequence"])
                    command = message.get("command", {})
                    if isinstance(command, dict):
                        session.record_input(sequence, command)
                        env = ClientCommandEnvelope(
                            session_id=session.server_session_id,
                            player_number=session._player_number,
                            client_sequence=sequence,
                            acknowledged_snapshot_sequence=session.acknowledged_snapshot_sequence,
                            simulation_tick=0,
                            issued_at=time.time(),
                            source="websocket",
                            commands={k: bool(v) for k, v in command.items() if k in INPUT_COMMAND_FIELDS},
                            session_token=session.server_session_token,
                        )
                        transport.sendto(encode_message(env))

                elif message_type in {"lobby_set_ready", "match_rematch", "chat_send"}:
                    if session.protocol_version < 2:
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("unsupported_capability", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    if not session._joined:
                        await _write_text(
                            writer,
                            json.dumps(
                                _error("not_joined", protocol=session.protocol_version),
                                separators=(",", ":"),
                            ),
                        )
                        continue
                    request_id = str(message["request_id"])
                    request: LobbySetReadyRequest | MatchRematchRequest | ChatSendRequest
                    if message_type == "lobby_set_ready":
                        request = LobbySetReadyRequest(
                            session_id=session.server_session_id,
                            player_number=session._player_number,
                            session_token=session.server_session_token,
                            request_id=request_id,
                            ready=bool(message["ready"]),
                        )
                    elif message_type == "match_rematch":
                        request = MatchRematchRequest(
                            session_id=session.server_session_id,
                            player_number=session._player_number,
                            session_token=session.server_session_token,
                            request_id=request_id,
                            ready=bool(message["ready"]),
                        )
                    else:
                        request = ChatSendRequest(
                            session_id=session.server_session_id,
                            player_number=session._player_number,
                            session_token=session.server_session_token,
                            request_id=request_id,
                            text=str(message["text"]),
                        )
                    transport.sendto(encode_message(request))

                elif message_type == "ping":
                    response = {
                        "type": "pong",
                        "protocol": session.protocol_version,
                        "sequence": int(message.get("sequence", 0)),
                        "client_time_msec": int(message.get("client_time_msec", 0)),
                        "server_time_msec": int(time.time() * 1000),
                    }
                    await _write_text(writer, json.dumps(response, separators=(",", ":")))

                elif message_type == "disconnect":
                    graceful_disconnect = True
                    await _write_text(
                        writer,
                        json.dumps(
                            {
                                "type": "disconnect",
                                "protocol": session.protocol_version,
                                "reason": str(message.get("reason", "client_disconnect")),
                            },
                            separators=(",", ":"),
                        ),
                    )
                    break
                else:
                    await _write_text(
                        writer,
                        json.dumps(_error("unknown_type", received_type=message_type), separators=(",", ":")),
                    )
        finally:
            try:
                from groundfire.network.codec import encode_message
            except ModuleNotFoundError:
                from src.groundfire.network.codec import encode_message

            disconnect_notice = session.disconnect_notice("client_disconnect") if graceful_disconnect else None
            if disconnect_notice is not None:
                transport.sendto(encode_message(disconnect_notice))
            udp_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await udp_task
            transport.close()
            session.close()
            writer.close()
            with contextlib.suppress(ConnectionError):
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
            or _optional_boolean_field(message, "spectator")
            or _optional_boolean_field(message, "is_computer")
        )
    if message_type == "input":
        shape_error = _required_integer_field(message, "sequence") or _required_dict_field(message, "command")
        if shape_error is not None:
            return shape_error
        return _validate_input_command(message["command"])
    if message_type == "session_resume":
        return (
            _required_string_field(message, "session_id")
            or _required_integer_field(message, "player_number")
            or _required_string_field(message, "resume_token")
            or _optional_string_field(message, "player_name")
        )
    if message_type in {"lobby_set_ready", "match_rematch"}:
        return _required_string_field(message, "request_id") or _required_boolean_field(message, "ready")
    if message_type == "chat_send":
        return _required_string_field(message, "request_id") or _required_string_field(message, "text")
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


def _required_boolean_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name not in message:
        return _error("missing_field", field=field_name)
    if not isinstance(message[field_name], bool):
        return _error("invalid_field", field=field_name, expected="boolean")
    return None


def _optional_boolean_field(message: dict[str, Any], field_name: str) -> dict[str, Any] | None:
    if field_name in message and not isinstance(message[field_name], bool):
        return _error("invalid_field", field=field_name, expected="boolean")
    return None


def _validate_input_command(command: dict[str, Any]) -> dict[str, Any] | None:
    for field_name, value in command.items():
        if field_name not in INPUT_COMMAND_FIELDS:
            return _error("unknown_command", command=field_name)
        if not isinstance(value, bool):
            return _error("invalid_command", command=field_name, expected="boolean")
    return None


def generate_join_token(
    session_secret: str,
    player_name: str,
    *,
    now: float | None = None,
    ttl_seconds: int = DEFAULT_SESSION_TOKEN_TTL_SECONDS,
) -> str:
    if not session_secret:
        raise ValueError("session_secret is required")
    issued_at = int(time.time() if now is None else now)
    claims = {
        "version": 1,
        "player_name": str(player_name),
        "player_key": _normalized_player_name(player_name),
        "issued_at": issued_at,
        "expires_at": issued_at + int(ttl_seconds),
    }
    payload = _base64url_encode(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    signature = _join_token_signature(session_secret, payload)
    return f"{SESSION_TOKEN_VERSION}.{payload}.{signature}"


def validate_join_token(
    token: str,
    session_secret: str,
    player_name: str,
    *,
    now: float | None = None,
) -> bool:
    if not token or not session_secret:
        return False
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != SESSION_TOKEN_VERSION:
        return False
    _prefix, payload, signature = parts
    expected_signature = _join_token_signature(session_secret, payload)
    if not hmac.compare_digest(signature, expected_signature):
        return False
    try:
        raw_claims = json.loads(_base64url_decode(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    if not isinstance(raw_claims, dict):
        return False
    expires_at = raw_claims.get("expires_at")
    if not isinstance(expires_at, int) or isinstance(expires_at, bool):
        return False
    current_time = int(time.time() if now is None else now)
    if expires_at < current_time:
        return False
    expected_player_key = _normalized_player_name(player_name)
    if str(raw_claims.get("player_key", "")) != expected_player_key:
        return False
    return True


def _auth_token_is_authorized(
    auth_token: str,
    *,
    required_auth_token: str,
    session_secret: str,
    player_name: str,
) -> bool:
    if not required_auth_token and not session_secret:
        return True
    if required_auth_token and hmac.compare_digest(auth_token, required_auth_token):
        return True
    if session_secret and validate_join_token(auth_token, session_secret, player_name):
        return True
    return False


def _auth_token_mode(required_auth_token: str, session_secret: str) -> str:
    if required_auth_token and session_secret:
        return "static_or_signed"
    if session_secret:
        return "signed"
    if required_auth_token:
        return "static"
    return "none"


def _redeem_admission_ticket(url: str, secret: str, ticket: str) -> bool:
    payload = json.dumps({"ticket": ticket}, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "X-Groundfire-Internal": secret},
    )
    try:
        with urllib.request.urlopen(request, timeout=2.0) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _join_token_signature(session_secret: str, payload: str) -> str:
    digest = hmac.new(
        session_secret.encode("utf-8"),
        f"{SESSION_TOKEN_VERSION}.{payload}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _snapshot_state_for_session(
    session: WebSocketGatewaySession,
    msg: Any,
    *,
    server_time_msec: int | None = None,
) -> dict[str, Any]:
    state = {
        "status": "joined",
        "player_name": session.player_name,
        "player_number": session._player_number,
        "role": session._role,
        "joined": True,
        "last_input": session.last_input,
        "server_time_msec": int(time.time() * 1000) if server_time_msec is None else server_time_msec,
        "match_snapshot_schema": MATCH_SNAPSHOT_SCHEMA_VERSION,
        "event_schema": EVENT_SCHEMA_VERSION,
        "session_id": session.server_session_id,
        "resume_token": session.server_session_token,
        "match_snapshot": _version_match_snapshot(msg.snapshot),
        "terrain_patches": [_version_terrain_patch(patch) for patch in msg.terrain_patches],
        "events": [_version_event(event) for event in msg.events],
    }
    state.update(session.join_registry.metadata())
    return state


def _version_match_snapshot(snapshot: object) -> dict[str, Any]:
    versioned = _plain_dict(snapshot, "match_snapshot")
    _ensure_schema_fields("match_snapshot", versioned, MATCH_SNAPSHOT_SCHEMA_REQUIRED_FIELDS)
    players = versioned.get("players", [])
    if not isinstance(players, list):
        raise ValueError("match_snapshot.players must be an array")
    for player in players:
        player_payload = _plain_dict(player, "match_snapshot.players[]")
        _ensure_schema_fields("match_snapshot.players[]", player_payload, REPLICATED_PLAYER_SCHEMA_REQUIRED_FIELDS)
    entities = versioned.get("entities", [])
    if not isinstance(entities, list):
        raise ValueError("match_snapshot.entities must be an array")
    for entity in entities:
        entity_payload = _plain_dict(entity, "match_snapshot.entities[]")
        _ensure_schema_fields("match_snapshot.entities[]", entity_payload, REPLICATED_ENTITY_SCHEMA_REQUIRED_FIELDS)
    return versioned


def _version_terrain_patch(patch: object) -> dict[str, Any]:
    versioned = _plain_dict(patch, "terrain_patches[]")
    _ensure_schema_fields("terrain_patches[]", versioned, TERRAIN_PATCH_SCHEMA_REQUIRED_FIELDS)
    return versioned


def _version_event(event: dict[str, Any]) -> dict[str, Any]:
    versioned = _plain_dict(event, "events[]")
    versioned.setdefault("schema", EVENT_SCHEMA_VERSION)
    payload = versioned.get("payload", {})
    versioned["payload"] = dict(payload) if isinstance(payload, dict) else {"value": payload}
    versioned["event_type"] = str(versioned.get("event_type", "unknown"))
    _ensure_schema_fields("events[]", versioned, EVENT_SCHEMA_REQUIRED_FIELDS)
    return versioned


def _plain_dict(value: object, label: str) -> dict[str, Any]:
    plain = to_plain(value)
    if not isinstance(plain, dict):
        raise ValueError(f"{label} must be an object")
    return dict(plain)


def _ensure_schema_fields(label: str, payload: dict[str, Any], required_fields: frozenset[str]) -> None:
    missing = sorted(required_fields.difference(payload))
    if missing:
        raise ValueError(f"{label} is missing required schema fields: {', '.join(missing)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Groundfire browser-safe WebSocket gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=27080)
    parser.add_argument(
        "--udp-host",
        default=os.environ.get("GROUNDFIRE_WEB_GATEWAY_UDP_HOST", "127.0.0.1"),
        help="The UDP host of the definitive ServerApp to proxy to.",
    )
    parser.add_argument(
        "--udp-port",
        type=_positive_int,
        default=_environment_positive_int("GROUNDFIRE_WEB_GATEWAY_UDP_PORT", 27015),
        help="The UDP port of the definitive ServerApp to proxy to.",
    )
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
        "--session-secret",
        default=os.environ.get("GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET", ""),
        help=(
            "Optional HMAC secret for signed expiring join tokens. "
            "Also configurable through GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET."
        ),
    )
    parser.add_argument(
        "--session-token-ttl",
        type=_positive_int,
        default=_environment_positive_int(
            "GROUNDFIRE_WEB_GATEWAY_SESSION_TOKEN_TTL",
            DEFAULT_SESSION_TOKEN_TTL_SECONDS,
        ),
        help=(
            "Lifetime, in seconds, for tokens generated by --issue-token. "
            "Also configurable through GROUNDFIRE_WEB_GATEWAY_SESSION_TOKEN_TTL."
        ),
    )
    parser.add_argument(
        "--issue-token",
        default="",
        metavar="PLAYER_NAME",
        help="Print a signed join token for PLAYER_NAME and exit. Requires --session-secret.",
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
    parser.add_argument(
        "--admission-redeem-url",
        default=os.environ.get("GROUNDFIRE_ADMISSION_REDEEM_URL", ""),
        help="Optional internal HTTP endpoint that consumes each managed admission ticket once.",
    )
    parser.add_argument(
        "--admission-secret",
        default=os.environ.get("GROUNDFIRE_ADMISSION_SECRET", ""),
        help="Internal credential used only with --admission-redeem-url.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.issue_token:
        if not args.session_secret:
            parser.error("--issue-token requires --session-secret or GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET")
        print(generate_join_token(args.session_secret, args.issue_token, ttl_seconds=args.session_token_ttl))
        return 0
    gateway = WebSocketGateway(
        args.host,
        args.port,
        password=args.password,
        auth_token=args.auth_token,
        session_secret=args.session_secret,
        max_players=args.max_players,
        closed=args.closed,
        banned_players=args.ban_player,
        udp_host=args.udp_host,
        udp_port=args.udp_port,
        admission_redeem_url=args.admission_redeem_url,
        admission_secret=args.admission_secret,
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


def _environment_positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
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
