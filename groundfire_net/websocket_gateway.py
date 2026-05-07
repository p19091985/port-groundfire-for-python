from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import struct
import time
from dataclasses import dataclass, field, replace
from typing import Any

from groundfire_net.codec import to_plain
from src.groundfire.sim.match import MatchState, ReplicatedPlayerState
from src.groundfire.sim.world import WorldState

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
PROTOCOL_VERSION = 1


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
            "sequence": self.sequence,
            "state": {
                "status": status,
                "player_name": self.player_name,
                "joined": self.tank_entity_id is not None,
                "last_input": self.last_input,
                "server_time_msec": int(time.time() * 1000),
                "match_snapshot": to_plain(snapshot),
                "terrain_patches": [to_plain(patch) for patch in self.world.drain_terrain_patches()],
                "events": list(self.match.drain_events()),
            },
        }


@dataclass
class WebSocketGatewaySession:
    simulation: GatewaySimulation = field(default_factory=GatewaySimulation)

    def handle_text(self, payload: str) -> list[dict[str, Any]]:
        try:
            message = json.loads(payload)
        except json.JSONDecodeError:
            return [_error("invalid_json")]
        if not isinstance(message, dict):
            return [_error("invalid_message")]

        message_type = str(message.get("type", ""))
        if message_type == "hello":
            return [
                {
                    "type": "hello",
                    "protocol": PROTOCOL_VERSION,
                    "server": "python-websocket-gateway",
                }
            ]
        if message_type == "join":
            self.simulation.join(str(message.get("player_name", self.simulation.player_name)))
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
                    "sequence": int(message.get("sequence", 0)),
                    "client_time_msec": int(message.get("client_time_msec", 0)),
                    "server_time_msec": int(time.time() * 1000),
                }
            ]
        if message_type == "disconnect":
            return [{"type": "disconnect", "reason": str(message.get("reason", "client_disconnect"))}]
        return [_error("unknown_type", received_type=message_type)]


class WebSocketGateway:
    def __init__(self, host: str = "127.0.0.1", port: int = 27080):
        self.host = host
        self.port = port

    async def serve_forever(self) -> None:
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        session = WebSocketGatewaySession()
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
    payload = {"type": "error", "message": message}
    payload.update(extra)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Groundfire browser-safe WebSocket gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=27080)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    asyncio.run(WebSocketGateway(args.host, args.port).serve_forever())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
