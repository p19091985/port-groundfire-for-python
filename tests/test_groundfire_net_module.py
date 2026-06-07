import asyncio
import base64
import hashlib
import json
import struct
import threading
import unittest
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from groundfire_net import (
    DirectoryServiceConfig,
    JsonDataclassCodec,
    ServerBook,
    ServerListEntry,
    build_http_server,
)
from groundfire_net.directory_service import (
    build_parser as build_directory_parser,
    directory_diagnostics,
    directory_server_errors,
    load_directory_payload,
    response_bytes,
    response_etag,
)
from groundfire_net.websocket_gateway import (
    DEFAULT_SESSION_TOKEN_TTL_SECONDS,
    EVENT_SCHEMA_VERSION,
    INPUT_COMMAND_FIELDS,
    MATCH_SNAPSHOT_SCHEMA_VERSION,
    MAX_PROTOCOL_VERSION,
    MIN_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    SESSION_TOKEN_VERSION,
    WebSocketGateway,
    WebSocketGatewaySession,
    build_parser,
    generate_join_token,
    main,
    validate_join_token,
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

    def test_directory_service_converts_server_book_to_schema_one(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "servers.json"
            book = ServerBook(path)
            book.set_internet_servers(
                (
                    ServerListEntry(
                        name="Public Gateway",
                        host="play.example.test",
                        port=443,
                        map_name="classic",
                        player_count=2,
                        max_players=8,
                        latency_ms=42,
                        source="internet",
                        requires_password=True,
                        region="world",
                        secure=True,
                        protocol_version=1,
                    ),
                )
            )

            payload = load_directory_payload(DirectoryServiceConfig(directory_path=path))
            server = payload["servers"][0]

            self.assertEqual(payload["schema"], 1)
            self.assertEqual(server["name"], "Public Gateway")
            self.assertEqual(server["players"], "2/8")
            self.assertEqual(server["latency"], "42ms")
            self.assertEqual(server["source"], "online")
            self.assertEqual(server["endpoint"], "wss://play.example.test:443")
            self.assertTrue(server["passworded"])

    def test_directory_service_injects_session_token_url_for_gateway_entry(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text('{"schema":1,"servers":[]}', encoding="utf-8")
            payload = load_directory_payload(
                DirectoryServiceConfig(
                    directory_path=path,
                    gateway_endpoint="wss://play.example.test/gateway",
                    session_secret="session-secret",
                    session_token_url="https://directory.example.test/session-token.json",
                )
            )

            server = payload["servers"][0]

            self.assertEqual(server["endpoint"], "wss://play.example.test/gateway")
            self.assertEqual(server["session_token_url"], "https://directory.example.test/session-token.json")

    def test_directory_service_serves_http_with_cache_headers(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "servers": [
                            {
                                "name": "Online",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "ws://127.0.0.1:8765",
                                "passworded": False,
                            },
                            {
                                "name": "LAN",
                                "game": "Groundfire",
                                "players": "0/8",
                                "map": "classic",
                                "latency": "LAN",
                                "source": "lan",
                                "endpoint": "127.0.0.1:27015",
                                "passworded": False,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            config = DirectoryServiceConfig(
                host="127.0.0.1",
                port=0,
                directory_path=path,
                gateway_endpoint="ws://127.0.0.1:9999",
                server_name="Injected Gateway",
                cache_seconds=17,
                refresh_seconds=23,
            )
            server = build_http_server(config)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                with urlopen(f"http://{host}:{port}/servers.json", timeout=5) as response:
                    body = response.read()
                    payload = json.loads(body.decode("utf-8"))
                    etag = response.headers["ETag"]
                    self.assertEqual(response.headers["Cache-Control"], "public, max-age=17, must-revalidate")
                    self.assertEqual(response.headers["X-Groundfire-Directory-Refresh"], "23")
                    self.assertEqual(etag, response_etag(body))
                    self.assertRegex(etag, r'^"[0-9a-f]{64}"$')
                    self.assertEqual(payload["schema"], 1)
                    self.assertEqual([item["name"] for item in payload["servers"]], ["Injected Gateway", "Online"])
                    self.assertFalse(any(item["source"] == "lan" for item in payload["servers"]))

                with urlopen(f"http://{host}:{port}/healthz", timeout=5) as response:
                    health = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(health["served_servers"], 2)
                    self.assertEqual(health["filtered_lan_servers"], 1)

                with urlopen(f"http://{host}:{port}/diagnostics.json", timeout=5) as response:
                    diagnostics = json.loads(response.read().decode("utf-8"))
                    self.assertTrue(diagnostics["ok"])
                    self.assertEqual(diagnostics["served_servers"], 2)
                    self.assertEqual(diagnostics["filtered_lan_servers"], 1)
                    self.assertFalse(diagnostics["invalid_servers"])

                request = Request(f"http://{host}:{port}/servers.json", headers={"If-None-Match": etag})
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=5)
                self.assertEqual(raised.exception.code, 304)

                request = Request(f"http://{host}:{port}/servers.json", headers={"If-None-Match": f'"old", {etag}'})
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=5)
                self.assertEqual(raised.exception.code, 304)

                request = Request(
                    f"http://{host}:{port}/servers.json",
                    headers={"If-None-Match": etag.strip('"')},
                )
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=5)
                self.assertEqual(raised.exception.code, 304)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_directory_service_issues_no_store_signed_session_token(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text('{"schema":1,"servers":[]}', encoding="utf-8")
            config = DirectoryServiceConfig(
                host="127.0.0.1",
                port=0,
                directory_path=path,
                session_secret="session-secret",
                session_token_ttl=45,
            )
            server = build_http_server(config)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address
                with urlopen(f"http://{host}:{port}/session-token.json?player_name=Alice%20One", timeout=5) as response:
                    payload = json.loads(response.read().decode("utf-8"))

                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    self.assertNotIn("ETag", response.headers)
                    self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
                    self.assertTrue(payload["ok"])
                    self.assertEqual(payload["token_type"], "groundfire_join")
                    self.assertEqual(payload["player_name"], "Alice One")
                    self.assertEqual(payload["expires_in"], 45)
                    self.assertTrue(validate_join_token(payload["auth_token"], "session-secret", "Alice One"))
                    self.assertFalse(validate_join_token(payload["auth_token"], "session-secret", "Bob"))

                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"http://{host}:{port}/session-token.json?player_name=", timeout=5)
                self.assertEqual(raised.exception.code, 400)
                self.assertEqual(json.loads(raised.exception.read().decode("utf-8"))["error"], "missing_player_name")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_directory_service_session_token_endpoint_is_opt_in(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text('{"schema":1,"servers":[]}', encoding="utf-8")
            server = build_http_server(DirectoryServiceConfig(host="127.0.0.1", port=0, directory_path=path))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host, port = server.server_address

                with self.assertRaises(HTTPError) as raised:
                    urlopen(f"http://{host}:{port}/session-token.json?player_name=Alice", timeout=5)

                self.assertEqual(raised.exception.code, 404)
                self.assertEqual(json.loads(raised.exception.read().decode("utf-8"))["error"], "session_tokens_disabled")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    def test_directory_service_filters_invalid_public_entries(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "servers": [
                            {
                                "name": "Valid Online",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "wss://play.example.test/gateway",
                                "passworded": False,
                            },
                            {
                                "name": "Invalid Online",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "https://play.example.test/gateway",
                                "passworded": False,
                            },
                            {
                                "name": "Local Dev",
                                "game": "Groundfire",
                                "players": "0/8",
                                "map": "classic",
                                "latency": "LAN",
                                "source": "lan",
                                "endpoint": "127.0.0.1:27015",
                                "passworded": False,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            public_payload = load_directory_payload(
                DirectoryServiceConfig(directory_path=path, gateway_endpoint="https://invalid.example.test")
            )
            dev_payload = load_directory_payload(DirectoryServiceConfig(directory_path=path, include_lan=True))
            diagnostics = directory_diagnostics(
                DirectoryServiceConfig(directory_path=path, gateway_endpoint="https://invalid.example.test")
            )

            self.assertEqual([server["name"] for server in public_payload["servers"]], ["Valid Online"])
            self.assertEqual([server["name"] for server in dev_payload["servers"]], ["Valid Online", "Local Dev"])
            self.assertFalse(diagnostics["ok"])
            self.assertEqual(diagnostics["accepted_servers"], 1)
            self.assertEqual(diagnostics["served_servers"], 1)
            self.assertEqual(diagnostics["filtered_lan_servers"], 1)
            self.assertTrue(diagnostics["invalid_gateway_endpoint"])
            self.assertEqual(diagnostics["invalid_servers"][0]["index"], 1)
            self.assertIn(
                "endpoint must be ws:// or wss:// for online servers",
                directory_server_errors(
                    {
                        "name": "Bad",
                        "game": "Groundfire",
                        "players": "1/8",
                        "map": "classic",
                        "latency": "20ms",
                        "source": "online",
                        "endpoint": "https://example.test",
                        "passworded": False,
                    }
                ),
            )

    def test_directory_service_rejects_static_auth_tokens_for_public_payloads_by_default(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "directory.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "servers": [
                            {
                                "name": "Static Secret",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "wss://play.example.test/static",
                                "passworded": False,
                                "auth_token": "shared-secret",
                            },
                            {
                                "name": "Signed Session",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "wss://play.example.test/signed",
                                "passworded": False,
                                "session_token_url": "https://directory.example.test/session-token.json",
                            },
                            {
                                "name": "Bad Issuer",
                                "game": "Groundfire",
                                "players": "1/8",
                                "map": "classic",
                                "latency": "20ms",
                                "source": "online",
                                "endpoint": "wss://play.example.test/bad-issuer",
                                "passworded": False,
                                "session_token_url": "file:///tmp/session-token.json",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            public_payload = load_directory_payload(DirectoryServiceConfig(directory_path=path))
            private_payload = load_directory_payload(
                DirectoryServiceConfig(directory_path=path, allow_static_auth_tokens=True)
            )
            diagnostics = directory_diagnostics(DirectoryServiceConfig(directory_path=path))

            self.assertEqual([server["name"] for server in public_payload["servers"]], ["Signed Session"])
            self.assertEqual([server["name"] for server in private_payload["servers"]], ["Static Secret", "Signed Session"])
            self.assertFalse(diagnostics["ok"])
            self.assertFalse(diagnostics["allow_static_auth_tokens"])
            self.assertEqual(diagnostics["accepted_servers"], 1)
            self.assertEqual(diagnostics["served_servers"], 1)
            self.assertEqual(diagnostics["invalid_servers"][0]["index"], 0)
            self.assertEqual(diagnostics["invalid_servers"][1]["index"], 2)
            self.assertIn(
                "auth_token is not allowed in public directory entries; use session_token_url",
                diagnostics["invalid_servers"][0]["errors"],
            )
            self.assertIn("session_token_url must be http:// or https://", diagnostics["invalid_servers"][1]["errors"])
            self.assertIn(
                "auth_token is not allowed in public directory entries; use session_token_url",
                directory_server_errors(
                    {
                        "name": "Static Secret",
                        "game": "Groundfire",
                        "players": "1/8",
                        "map": "classic",
                        "latency": "20ms",
                        "source": "online",
                        "endpoint": "wss://play.example.test/static",
                        "passworded": False,
                        "auth_token": "shared-secret",
                    },
                    allow_static_auth_tokens=False,
                ),
            )

    def test_directory_service_response_etag_is_stable(self):
        payload = {"schema": 1, "servers": []}

        self.assertEqual(response_etag(response_bytes(payload)), response_etag(response_bytes(payload)))



    def test_signed_join_token_validation_checks_signature_expiry_and_player(self):
        token = generate_join_token("session-secret", "Alice", now=1000, ttl_seconds=30)
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

        self.assertTrue(validate_join_token(token, "session-secret", "Alice", now=1030))
        self.assertFalse(validate_join_token(token, "session-secret", "Alice", now=1031))
        self.assertFalse(validate_join_token(token, "wrong-secret", "Alice", now=1005))
        self.assertFalse(validate_join_token(token, "session-secret", "Bob", now=1005))
        self.assertFalse(validate_join_token(tampered, "session-secret", "Alice", now=1005))


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
            "--session-secret",
            "signing-secret",
            "--session-token-ttl",
            "90",
            "--issue-token",
            "Alice",
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
        self.assertEqual(args.session_secret, "signing-secret")
        self.assertEqual(args.session_token_ttl, 90)
        self.assertEqual(args.issue_token, "Alice")
        self.assertEqual(args.max_players, 4)
        self.assertTrue(args.closed)
        self.assertEqual(args.ban_player, ["Mallory"])


    def test_directory_service_parser_exposes_session_token_options(self):
        args = build_directory_parser().parse_args([
            "--session-secret",
            "directory-secret",
            "--session-token-ttl",
            "120",
            "--session-token-url",
            "https://directory.example.test/session-token.json",
            "--allow-static-auth-tokens",
        ])

        self.assertEqual(args.session_secret, "directory-secret")
        self.assertEqual(args.session_token_ttl, 120)
        self.assertEqual(args.session_token_url, "https://directory.example.test/session-token.json")
        self.assertTrue(args.allow_static_auth_tokens)




    def test_godot_migration_strategy_documents_gateway_contract(self):
        doc = (PROJECT_ROOT / "docs" / "godot_migration_strategy.md").read_text(encoding="utf-8")

        self.assertIn("Current protocol: `1`", doc)
        self.assertIn("Supported protocol range: `1..1`", doc)
        self.assertIn("supported_protocols", doc)
        self.assertIn("password_required", doc)
        self.assertIn("auth_required", doc)
        self.assertIn("auth_token", doc)
        self.assertIn("auth_token_mode", doc)
        self.assertIn("--session-secret", doc)
        self.assertIn("--issue-token", doc)
        self.assertIn("/session-token.json", doc)
        self.assertIn("GROUNDFIRE_DIRECTORY_SESSION_SECRET", doc)
        self.assertIn("--allow-static-auth-tokens", doc)
        self.assertIn("GROUNDFIRE_DIRECTORY_ALLOW_STATIC_AUTH_TOKENS", doc)
        self.assertIn("rejects embedded `auth_token` entries by default", doc)
        self.assertIn("signed session tokens", doc)
        self.assertIn("GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET", doc)
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
            {"type": "input", "protocol": 1, "sequence": 3, "command": {"move_right": True, "shield": False}},
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
