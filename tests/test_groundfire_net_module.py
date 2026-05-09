import asyncio
import base64
import hashlib
import json
import struct
import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from groundfire_net import JsonDataclassCodec, ServerBook, ServerListEntry
from groundfire_net.websocket_gateway import (
    GatewayJoinRegistry,
    GatewaySimulation,
    WebSocketGateway,
    WebSocketGatewaySession,
    build_parser,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ExampleMessage:
    name: str
    value: int


class GroundfireNetModuleTests(unittest.TestCase):
    def test_json_codec_uses_standard_library_envelopes(self):
        codec = JsonDataclassCodec(lambda message_type, payload: ExampleMessage(**payload))
        message = ExampleMessage(name="hello", value=7)

        encoded = codec.encode(message)
        decoded = codec.decode(encoded)

        self.assertIn(b"ExampleMessage", encoded)
        self.assertEqual(decoded, message)

    def test_server_book_persists_favorites_and_history(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "servers.json"
            book = ServerBook(path)
            entry = ServerListEntry(name="Local", host="127.0.0.1", port=27015)

            book.add_favorite(entry)
            book.record_history(entry)
            reloaded = ServerBook(path)

            self.assertEqual(reloaded.get_favorites()[0].endpoint, "127.0.0.1:27015")
            self.assertEqual(reloaded.get_history()[0].name, "Local")
            self.assertRegex(reloaded.get_history()[0].last_played, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")

    def test_server_book_persists_internet_list_and_password_flag(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "servers.json"
            book = ServerBook(path)
            entry = ServerListEntry(
                name="Public",
                host="203.0.113.1",
                port=27015,
                source="lan",
                requires_password=True,
                region="sa",
                secure=False,
            )

            book.set_internet_servers((entry,))
            reloaded = ServerBook(path)

            self.assertEqual(reloaded.get_internet()[0].source, "internet")
            self.assertTrue(reloaded.get_internet()[0].requires_password)
            self.assertEqual(reloaded.get_internet()[0].region, "sa")
            self.assertFalse(reloaded.get_internet()[0].secure)
            self.assertEqual(reloaded.entries_for_tab("internet")[0].endpoint, "203.0.113.1:27015")

    def test_websocket_gateway_session_speaks_godot_message_contract(self):
        session = WebSocketGatewaySession()

        hello = session.handle_text('{"type":"hello","protocol":1,"client":"godot"}')
        joined = session.handle_text('{"type":"join","protocol":1,"player_name":"GodotPlayer","password":""}')
        input_response = session.handle_text(
            '{"type":"input","protocol":1,"sequence":7,"command":{"fire":true,"aim_left":false}}'
        )
        pong = session.handle_text('{"type":"ping","protocol":1,"sequence":8,"client_time_msec":1234}')

        self.assertEqual(hello[0]["type"], "hello")
        self.assertEqual(hello[0]["protocol"], 1)
        self.assertEqual(hello[0]["min_protocol"], 1)
        self.assertEqual(hello[0]["max_protocol"], 1)
        self.assertEqual(hello[0]["supported_protocols"], [1])
        self.assertEqual(hello[0]["match_snapshot_schema"], 1)
        self.assertEqual(hello[0]["event_schema"], 1)
        self.assertFalse(hello[0]["password_required"])
        self.assertTrue(hello[0]["joins_open"])
        self.assertFalse(hello[0]["ban_enforced"])
        self.assertEqual(hello[0]["max_players"], 0)
        self.assertEqual(hello[0]["players_connected"], 0)
        self.assertEqual(joined[0]["type"], "snapshot")
        self.assertEqual(joined[0]["protocol"], 1)
        self.assertEqual(joined[0]["state"]["player_name"], "GodotPlayer")
        self.assertEqual(joined[0]["state"]["match_snapshot_schema"], 1)
        self.assertEqual(joined[0]["state"]["event_schema"], 1)
        self.assertEqual(joined[0]["state"]["match_snapshot"]["players"][0]["name"], "GodotPlayer")
        self.assertEqual(joined[0]["state"]["match_snapshot"]["entities"][0]["entity_type"], "tank")
        self.assertEqual(input_response[0]["sequence"], 7)
        self.assertEqual(input_response[0]["state"]["last_input"]["fire"], True)
        self.assertEqual(input_response[0]["state"]["match_snapshot"]["simulation_tick"], 1)
        self.assertEqual(pong[0]["type"], "pong")
        self.assertEqual(pong[0]["protocol"], 1)
        self.assertEqual(pong[0]["client_time_msec"], 1234)

    def test_websocket_gateway_speaks_contract_over_real_frames(self):
        messages = asyncio.run(_exercise_websocket_gateway_over_tcp())

        connected, hello, rejected, joined, input_response, pong, disconnect = messages

        self.assertEqual(connected["type"], "snapshot")
        self.assertEqual(connected["protocol"], 1)
        self.assertEqual(connected["state"]["status"], "connected")
        self.assertEqual(hello["type"], "hello")
        self.assertTrue(hello["password_required"])
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["message"], "invalid_password")
        self.assertEqual(joined["type"], "snapshot")
        self.assertEqual(joined["state"]["status"], "joined")
        self.assertEqual(joined["state"]["player_name"], "GodotPlayer")
        self.assertEqual(input_response["sequence"], 3)
        self.assertTrue(input_response["state"]["last_input"]["move_right"])
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["sequence"], 4)
        self.assertEqual(disconnect["type"], "disconnect")
        self.assertEqual(disconnect["reason"], "test_done")

    def test_websocket_gateway_session_rejects_invalid_password(self):
        session = WebSocketGatewaySession(required_password="secret")

        hello = session.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        rejected = session.handle_text('{"type":"join","protocol":1,"player_name":"Mallory","password":"wrong"}')[0]

        self.assertTrue(hello["password_required"])
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["protocol"], 1)
        self.assertEqual(rejected["message"], "invalid_password")
        self.assertIsNone(session.simulation.tank_entity_id)

        joined = session.handle_text('{"type":"join","protocol":1,"player_name":"Alice","password":"secret"}')[0]

        self.assertEqual(joined["type"], "snapshot")
        self.assertEqual(joined["state"]["player_name"], "Alice")

    def test_websocket_gateway_session_rejects_authentication_failure(self):
        session = WebSocketGatewaySession(required_auth_token="token-123")

        hello = session.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        rejected = session.handle_text('{"type":"join","protocol":1,"player_name":"Mallory","password":""}')[0]

        self.assertTrue(hello["auth_required"])
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["protocol"], 1)
        self.assertEqual(rejected["message"], "authentication_failed")
        self.assertIsNone(session.simulation.tank_entity_id)

        joined = session.handle_text(
            '{"type":"join","protocol":1,"player_name":"Alice","password":"","auth_token":"token-123"}'
        )[0]

        self.assertEqual(joined["type"], "snapshot")
        self.assertEqual(joined["state"]["player_name"], "Alice")

    def test_websocket_gateway_session_rejects_server_full_until_slot_released(self):
        registry = GatewayJoinRegistry(max_players=1)
        first = WebSocketGatewaySession(join_registry=registry)
        second = WebSocketGatewaySession(join_registry=registry)

        first_hello = first.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        first_join = first.handle_text('{"type":"join","protocol":1,"player_name":"Alice","password":""}')[0]
        second_hello = second.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        rejected = second.handle_text('{"type":"join","protocol":1,"player_name":"Bob","password":""}')[0]

        self.assertEqual(first_hello["max_players"], 1)
        self.assertEqual(first_hello["players_connected"], 0)
        self.assertEqual(first_join["type"], "snapshot")
        self.assertEqual(second_hello["players_connected"], 1)
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["message"], "server_full")
        self.assertEqual(rejected["max_players"], 1)
        self.assertEqual(rejected["players_connected"], 1)
        self.assertIsNone(second.simulation.tank_entity_id)

        first.close()
        second_join = second.handle_text('{"type":"join","protocol":1,"player_name":"Bob","password":""}')[0]

        self.assertEqual(second_join["type"], "snapshot")
        self.assertEqual(second_join["state"]["player_name"], "Bob")
        self.assertEqual(registry.active_players, 1)
        second.close()
        self.assertEqual(registry.active_players, 0)

    def test_websocket_gateway_session_rejects_server_closed(self):
        session = WebSocketGatewaySession(joins_closed=True)

        hello = session.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        rejected = session.handle_text('{"type":"join","protocol":1,"player_name":"Alice","password":""}')[0]

        self.assertFalse(hello["joins_open"])
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["protocol"], 1)
        self.assertEqual(rejected["message"], "server_closed")
        self.assertIsNone(session.simulation.tank_entity_id)

    def test_websocket_gateway_session_rejects_banned_player(self):
        session = WebSocketGatewaySession(banned_players=frozenset({"mallory"}))

        hello = session.handle_text('{"type":"hello","protocol":1,"client":"godot"}')[0]
        rejected = session.handle_text('{"type":"join","protocol":1,"player_name":"Mallory","password":""}')[0]
        joined = session.handle_text('{"type":"join","protocol":1,"player_name":"Alice","password":""}')[0]

        self.assertTrue(hello["ban_enforced"])
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["protocol"], 1)
        self.assertEqual(rejected["message"], "banned")
        self.assertEqual(joined["type"], "snapshot")
        self.assertEqual(joined["state"]["player_name"], "Alice")

    def test_websocket_gateway_parser_exposes_optional_password(self):
        args = build_parser().parse_args([
            "--host",
            "0.0.0.0",
            "--port",
            "27999",
            "--password",
            "secret",
            "--auth-token",
            "token-123",
            "--max-players",
            "4",
            "--closed",
            "--ban-player",
            "Mallory",
        ])

        self.assertEqual(args.host, "0.0.0.0")
        self.assertEqual(args.port, 27999)
        self.assertEqual(args.password, "secret")
        self.assertEqual(args.auth_token, "token-123")
        self.assertEqual(args.max_players, 4)
        self.assertTrue(args.closed)
        self.assertEqual(args.ban_player, ["Mallory"])

    def test_gateway_simulation_replicates_tank_and_terrain_state(self):
        simulation = GatewaySimulation()

        simulation.join("Player One")
        initial = simulation.snapshot(status="joined")
        simulation.apply_input(1, {"move_right": True, "aim_left": True})
        moved = simulation.snapshot(status="input")
        simulation.apply_input(2, {"fire": True})
        fired = simulation.snapshot(status="input")

        initial_tank = initial["state"]["match_snapshot"]["entities"][0]
        moved_tank = moved["state"]["match_snapshot"]["entities"][0]
        fired_entities = fired["state"]["match_snapshot"]["entities"]
        self.assertGreater(moved_tank["position"][0], initial_tank["position"][0])
        self.assertGreater(moved_tank["angle"], initial_tank["angle"])
        self.assertTrue(any(entity["entity_type"] == "projectile" for entity in fired_entities))
        self.assertGreaterEqual(fired["state"]["match_snapshot"]["terrain_revision"], 1)
        self.assertEqual(fired["state"]["match_snapshot_schema"], 1)
        self.assertEqual(fired["state"]["event_schema"], 1)
        self.assertEqual(fired["state"]["events"][0]["schema"], 1)
        self.assertEqual(fired["state"]["events"][0]["event_type"], "terrain_explosion")

    def test_websocket_gateway_session_reports_bad_messages(self):
        session = WebSocketGatewaySession()

        self.assertEqual(session.handle_text("not-json")[0]["message"], "invalid_json")
        self.assertEqual(session.handle_text('{"type":"wat","protocol":1}')[0]["received_type"], "wat")
        self.assertEqual(session.handle_text('{"type":"hello"}')[0]["message"], "missing_protocol")
        invalid_protocol = session.handle_text('{"type":"hello","protocol":true}')[0]
        self.assertEqual(invalid_protocol["message"], "invalid_protocol")
        self.assertEqual(invalid_protocol["expected_protocol"], 1)
        mismatch = session.handle_text('{"type":"hello","protocol":99}')[0]
        self.assertEqual(mismatch["message"], "protocol_mismatch")
        self.assertEqual(mismatch["expected_protocol"], 1)
        self.assertEqual(mismatch["min_protocol"], 1)
        self.assertEqual(mismatch["max_protocol"], 1)
        self.assertEqual(mismatch["supported_protocols"], [1])
        self.assertEqual(mismatch["received_protocol"], 99)

    def test_websocket_gateway_session_validates_message_shapes(self):
        session = WebSocketGatewaySession()

        missing_player = session.handle_text('{"type":"join","protocol":1}')[0]
        invalid_sequence = session.handle_text('{"type":"input","protocol":1,"sequence":"7","command":{}}')[0]
        invalid_command = session.handle_text('{"type":"input","protocol":1,"sequence":7,"command":true}')[0]
        unknown_command = session.handle_text('{"type":"input","protocol":1,"sequence":7,"command":{"crouch":true}}')[0]
        invalid_command_value = session.handle_text(
            '{"type":"input","protocol":1,"sequence":7,"command":{"fire":"yes"}}'
        )[0]
        missing_ping_time = session.handle_text('{"type":"ping","protocol":1,"sequence":8}')[0]
        invalid_disconnect = session.handle_text('{"type":"disconnect","protocol":1,"reason":404}')[0]

        self.assertEqual(missing_player["message"], "missing_field")
        self.assertEqual(missing_player["field"], "player_name")
        self.assertEqual(invalid_sequence["message"], "invalid_field")
        self.assertEqual(invalid_sequence["field"], "sequence")
        self.assertEqual(invalid_sequence["expected"], "integer")
        self.assertEqual(invalid_command["message"], "invalid_field")
        self.assertEqual(invalid_command["field"], "command")
        self.assertEqual(invalid_command["expected"], "object")
        self.assertEqual(unknown_command["message"], "unknown_command")
        self.assertEqual(unknown_command["command"], "crouch")
        self.assertEqual(invalid_command_value["message"], "invalid_command")
        self.assertEqual(invalid_command_value["command"], "fire")
        self.assertEqual(invalid_command_value["expected"], "boolean")
        self.assertEqual(missing_ping_time["message"], "missing_field")
        self.assertEqual(missing_ping_time["field"], "client_time_msec")
        self.assertEqual(invalid_disconnect["message"], "invalid_field")
        self.assertEqual(invalid_disconnect["field"], "reason")

    def test_godot_websocket_protocol_document_matches_gateway_contract(self):
        doc = (PROJECT_ROOT / "docs" / "godot_websocket_protocol.md").read_text(encoding="utf-8")

        self.assertIn("Current protocol: `1`", doc)
        self.assertIn("Supported protocol range: `1..1`", doc)
        self.assertIn("supported_protocols", doc)
        self.assertIn("password_required", doc)
        self.assertIn("auth_required", doc)
        self.assertIn("auth_token", doc)
        self.assertIn("joins_open", doc)
        self.assertIn("ban_enforced", doc)
        self.assertIn("max_players", doc)
        self.assertIn("players_connected", doc)
        self.assertIn("invalid_password", doc)
        self.assertIn("authentication_failed", doc)
        self.assertIn("server_full", doc)
        self.assertIn("server_closed", doc)
        self.assertIn("banned", doc)
        self.assertIn("missing_protocol", doc)
        self.assertIn("protocol_mismatch", doc)
        self.assertIn("missing_field", doc)
        self.assertIn("invalid_field", doc)
        self.assertIn("match_snapshot_schema", doc)
        self.assertIn("event_schema", doc)
        self.assertIn('"type": "snapshot"', doc)
        self.assertIn("match_snapshot", doc)


async def _exercise_websocket_gateway_over_tcp() -> list[dict]:
    gateway = WebSocketGateway(password="secret")
    server = await asyncio.start_server(gateway._handle_client, gateway.host, 0)
    host, port = server.sockets[0].getsockname()[:2]
    reader, writer = await asyncio.open_connection(host, port)
    try:
        await _send_websocket_handshake(reader, writer, host, port)
        messages = [await _read_server_message(reader)]
        for message in (
            {"type": "hello", "protocol": 1, "client": "godot"},
            {"type": "join", "protocol": 1, "player_name": "GodotPlayer", "password": "wrong"},
            {"type": "join", "protocol": 1, "player_name": "GodotPlayer", "password": "secret"},
            {"type": "input", "protocol": 1, "sequence": 3, "command": {"move_right": True}},
            {"type": "ping", "protocol": 1, "sequence": 4, "client_time_msec": 1234},
            {"type": "disconnect", "protocol": 1, "reason": "test_done"},
        ):
            await _write_client_message(writer, message)
            messages.append(await _read_server_message(reader))
        return messages
    finally:
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()


async def _send_websocket_handshake(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    host: str,
    port: int,
) -> None:
    key = base64.b64encode(b"groundfire-test!").decode("ascii")
    expected_accept = base64.b64encode(
        hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")
    writer.write(
        (
            "GET /gateway HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).encode("ascii")
    )
    await writer.drain()
    response = await reader.readuntil(b"\r\n\r\n")
    response_text = response.decode("ascii", errors="replace")
    if "101 Switching Protocols" not in response_text or expected_accept not in response_text:
        raise AssertionError(f"Unexpected WebSocket handshake response: {response_text}")


async def _write_client_message(writer: asyncio.StreamWriter, message: dict) -> None:
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    mask = b"\x11\x22\x33\x44"
    header = bytearray([0x81])
    if len(payload) < 126:
        header.append(0x80 | len(payload))
    elif len(payload) < 65536:
        header.append(0x80 | 126)
        header.extend(struct.pack("!H", len(payload)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack("!Q", len(payload)))
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    writer.write(bytes(header) + mask + masked)
    await writer.drain()


async def _read_server_message(reader: asyncio.StreamReader) -> dict:
    payload = await _read_unmasked_server_frame(reader)
    return json.loads(payload)


async def _read_unmasked_server_frame(reader: asyncio.StreamReader) -> str:
    header = await reader.readexactly(2)
    first, second = header
    opcode = first & 0x0F
    if opcode != 0x1:
        raise AssertionError(f"Unexpected server WebSocket opcode: {opcode}")
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    payload = await reader.readexactly(length)
    return payload.decode("utf-8")


if __name__ == "__main__":
    unittest.main()
