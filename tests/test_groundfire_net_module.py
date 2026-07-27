import asyncio
import base64
import hashlib
import json
import struct
import threading
import unittest
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from src.groundfire.network.codec import decode_message, encode_message
from src.groundfire.network.messages import (
    ClientCommandEnvelope,
    HelloRequest,
    JoinAccept,
    JoinRequest,
    ServerSnapshotEnvelope,
)
from src.groundfire.sim.match import MatchSnapshot, ReplicatedPlayerState
from src.groundfire.sim.world import ReplicatedEntityState, TerrainPatch

from groundfire_net import (
    DirectoryServiceConfig,
    GroundfireEventLogger,
    JsonDataclassCodec,
    ServerBook,
    ServerListEntry,
    build_http_server,
)
from groundfire_net.directory_service import (
    build_parser as build_directory_parser,
)
from groundfire_net.directory_service import (
    directory_diagnostics,
    directory_server_errors,
    load_directory_payload,
    response_bytes,
    response_etag,
)
from groundfire_net.websocket_gateway import (
    EVENT_SCHEMA_REQUIRED_FIELDS,
    EVENT_SCHEMA_VERSION,
    MATCH_SNAPSHOT_SCHEMA_REQUIRED_FIELDS,
    MATCH_SNAPSHOT_SCHEMA_VERSION,
    MAX_PROTOCOL_VERSION,
    MIN_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    REPLICATED_ENTITY_SCHEMA_REQUIRED_FIELDS,
    REPLICATED_PLAYER_SCHEMA_REQUIRED_FIELDS,
    SUPPORTED_PROTOCOL_VERSIONS,
    TERRAIN_PATCH_SCHEMA_REQUIRED_FIELDS,
    GatewayJoinRegistry,
    WebSocketGateway,
    WebSocketGatewaySession,
    _snapshot_state_for_session,
    build_parser,
    generate_join_token,
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
            self.assertEqual(reloaded.storage_path, Path(temp_dir) / "servers.sqlite3")
            self.assertTrue(reloaded.storage_path.exists())
            self.assertFalse(path.exists())

    def test_server_book_imports_legacy_json_into_sqlite(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "servers.json"
            path.write_text(
                json.dumps(
                    {
                        "favorites": [
                            {
                                "name": "Legacy",
                                "host": "127.0.0.1",
                                "port": 27016,
                            }
                        ],
                        "history": [],
                        "internet": [],
                    }
                ),
                encoding="utf-8",
            )

            book = ServerBook(path)

            self.assertEqual(book.get_favorites()[0].endpoint, "127.0.0.1:27016")
            self.assertEqual(book.storage_path, Path(temp_dir) / "servers.sqlite3")
            self.assertTrue(book.storage_path.exists())

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

    def test_directory_service_reads_sqlite_server_book_directly(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "servers.sqlite3"
            book = ServerBook(path)
            book.set_internet_servers(
                (
                    ServerListEntry(
                        name="SQLite Gateway",
                        host="play.example.test",
                        port=443,
                        map_name="classic",
                        source="internet",
                        secure=True,
                    ),
                )
            )

            payload = load_directory_payload(DirectoryServiceConfig(directory_path=path))

            self.assertEqual(payload["servers"][0]["name"], "SQLite Gateway")
            self.assertEqual(payload["servers"][0]["endpoint"], "wss://play.example.test:443")

    def test_event_logger_can_emit_structured_json_lines(self):
        stream = StringIO()
        logger = GroundfireEventLogger("groundfire-test", stream=stream, json_lines=True, run_id="run-1")

        logger("join_accept player_number=2 computer=false player_name='Ana Maria'")

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["component"], "groundfire-test")
        self.assertEqual(payload["event"], "join_accept")
        self.assertEqual(payload["run_id"], "run-1")
        self.assertEqual(payload["fields"]["player_number"], 2)
        self.assertFalse(payload["fields"]["computer"])
        self.assertEqual(payload["fields"]["player_name"], "Ana Maria")

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
                self.assertEqual(
                    json.loads(raised.exception.read().decode("utf-8"))["error"],
                    "session_tokens_disabled",
                )
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
            self.assertEqual(
                [server["name"] for server in private_payload["servers"]],
                ["Static Secret", "Signed Session"],
            )
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

    def test_websocket_gateway_session_enforces_join_policy_and_releases_slots(self):
        registry = GatewayJoinRegistry(max_players=1)
        first = WebSocketGatewaySession(required_password="secret", join_registry=registry)
        second = WebSocketGatewaySession(required_password="secret", join_registry=registry)

        self.assertEqual(
            first.prepare_join({"player_name": "Alice", "password": "wrong"})["message"],
            "invalid_password",
        )
        self.assertIsNone(first.prepare_join({"player_name": "Alice", "password": "secret"}))
        self.assertEqual(first._player_number, 1)
        self.assertEqual(first.hello_response()["players_connected"], 1)
        self.assertEqual(
            second.prepare_join({"player_name": "Bob", "password": "secret"})["message"],
            "server_full",
        )

        first.confirm_join(1, session_id="test-session", session_token="session-token")
        first.close()

        self.assertIsNone(second.prepare_join({"player_name": "Bob", "password": "secret"}))
        self.assertEqual(second._player_number, 1)

    def test_websocket_gateway_session_accepts_signed_expiring_auth_token(self):
        token = generate_join_token("session-secret", "Alice", ttl_seconds=60)
        wrong_player_token = generate_join_token("session-secret", "Bob", ttl_seconds=60)
        expired_token = generate_join_token("session-secret", "Alice", ttl_seconds=-1)
        session = WebSocketGatewaySession(session_secret="session-secret")

        self.assertTrue(session.hello_response()["auth_required"])
        self.assertEqual(session.hello_response()["auth_token_mode"], "signed")
        self.assertEqual(session.prepare_join({"player_name": "Alice"})["message"], "authentication_failed")
        self.assertEqual(
            session.prepare_join({"player_name": "Alice", "auth_token": wrong_player_token})["message"],
            "authentication_failed",
        )
        self.assertEqual(
            session.prepare_join({"player_name": "Alice", "auth_token": expired_token})["message"],
            "authentication_failed",
        )
        self.assertIsNone(session.prepare_join({"player_name": "Alice", "auth_token": token}))
        self.assertEqual(session.player_name, "Alice")

    def test_websocket_gateway_advertises_protocol_compatibility_window(self):
        hello = WebSocketGatewaySession().hello_response()

        self.assertEqual(hello["protocol"], PROTOCOL_VERSION)
        self.assertEqual(hello["min_protocol"], MIN_PROTOCOL_VERSION)
        self.assertEqual(hello["max_protocol"], MAX_PROTOCOL_VERSION)
        self.assertEqual(hello["supported_protocols"], list(SUPPORTED_PROTOCOL_VERSIONS))
        self.assertEqual(
            hello["supported_protocols"],
            list(range(MIN_PROTOCOL_VERSION, MAX_PROTOCOL_VERSION + 1)),
        )
        self.assertEqual(hello["match_snapshot_schema"], MATCH_SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(hello["event_schema"], EVENT_SCHEMA_VERSION)

    def test_websocket_gateway_versions_schema_one_snapshot_payloads(self):
        session = WebSocketGatewaySession()
        session.player_name = "GodotPlayer"
        session._player_number = 1
        session.last_input_sequence = 3
        session.last_input = {"move_right": True}
        envelope = _snapshot_envelope(
            "GodotPlayer",
            snapshot_sequence=7,
            acknowledged_command_sequence=3,
            terrain_patches=(
                TerrainPatch(
                    patch_id=1,
                    chunk_index=2,
                    operation="explosion",
                    payload={"revision": 7, "radius": 4.0},
                ),
            ),
            events=({"event_type": "terrain_explosion", "payload": {"position": [1.0, 2.0]}},),
        )

        state = _snapshot_state_for_session(session, envelope, server_time_msec=123456)
        snapshot = state["match_snapshot"]
        player = snapshot["players"][0]
        entity = snapshot["entities"][0]
        terrain_patch = state["terrain_patches"][0]
        event = state["events"][0]

        self.assertEqual(state["match_snapshot_schema"], MATCH_SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(state["event_schema"], EVENT_SCHEMA_VERSION)
        self.assertTrue(MATCH_SNAPSHOT_SCHEMA_REQUIRED_FIELDS.issubset(snapshot))
        self.assertTrue(REPLICATED_PLAYER_SCHEMA_REQUIRED_FIELDS.issubset(player))
        self.assertTrue(REPLICATED_ENTITY_SCHEMA_REQUIRED_FIELDS.issubset(entity))
        self.assertTrue(TERRAIN_PATCH_SCHEMA_REQUIRED_FIELDS.issubset(terrain_patch))
        self.assertTrue(EVENT_SCHEMA_REQUIRED_FIELDS.issubset(event))
        self.assertEqual(event["schema"], EVENT_SCHEMA_VERSION)
        self.assertEqual(event["event_type"], "terrain_explosion")
        self.assertEqual(event["payload"], {"position": [1.0, 2.0]})
        self.assertEqual(state["last_input"], {"move_right": True})
        self.assertEqual(state["server_time_msec"], 123456)

    def test_websocket_gateway_speaks_contract_over_real_frames_and_udp_proxy(self):
        messages, udp_messages = asyncio.run(_exercise_websocket_gateway_over_tcp())

        hello, rejected, joined, input_response, pong, disconnect = messages

        self.assertEqual(hello["type"], "hello")
        self.assertTrue(hello["password_required"])
        self.assertEqual(hello["server"], "python-websocket-proxy")
        self.assertEqual(rejected["type"], "error")
        self.assertEqual(rejected["message"], "invalid_password")
        self.assertEqual(joined["type"], "snapshot")
        self.assertEqual(joined["state"]["status"], "joined")
        self.assertEqual(joined["state"]["player_name"], "GodotPlayer")
        self.assertEqual(joined["state"]["player_number"], 1)
        self.assertEqual(joined["state"]["match_snapshot"]["players"][0]["name"], "GodotPlayer")
        self.assertEqual(input_response["sequence"], 3)
        self.assertTrue(input_response["state"]["last_input"]["move_right"])
        self.assertEqual(input_response["state"]["match_snapshot"]["players"][0]["acknowledged_command_sequence"], 3)
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["sequence"], 4)
        self.assertEqual(disconnect["type"], "disconnect")
        self.assertEqual(disconnect["reason"], "test_done")

        self.assertTrue(any(isinstance(message, HelloRequest) for message in udp_messages))
        join_requests = [message for message in udp_messages if isinstance(message, JoinRequest)]
        command_envelopes = [message for message in udp_messages if isinstance(message, ClientCommandEnvelope)]
        self.assertEqual(join_requests[0].player_name, "GodotPlayer")
        self.assertEqual(join_requests[0].password, "secret")
        self.assertIsNone(join_requests[0].requested_slot)
        self.assertEqual(command_envelopes[0].client_sequence, 3)
        self.assertEqual(command_envelopes[0].acknowledged_snapshot_sequence, 1)
        self.assertEqual(command_envelopes[0].commands, {"move_right": True, "shield": False})

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
        self.assertIn("Compatibility Policy", doc)
        self.assertIn("highest mutually supported protocol", doc)
        self.assertIn("No silent downgrade or upgrade", doc)
        self.assertIn(
            "normal public compatibility window keeps the current published protocol and the previous public protocol",
            doc,
        )
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


class _FakeGroundfireUdpProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.messages: list[object] = []
        self.transport = None

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr) -> None:
        message = decode_message(data)
        self.messages.append(message)
        if self.transport is None:
            return
        if isinstance(message, JoinRequest):
            self.transport.sendto(
                encode_message(JoinAccept(session_id="test-session", player_number=1, session_token="session-token")),
                addr,
            )
            self.transport.sendto(encode_message(_snapshot_envelope("GodotPlayer", snapshot_sequence=1)), addr)
        elif isinstance(message, ClientCommandEnvelope):
            self.transport.sendto(
                encode_message(
                    _snapshot_envelope(
                        "GodotPlayer",
                        snapshot_sequence=2,
                        acknowledged_command_sequence=message.client_sequence,
                    )
                ),
                addr,
            )


async def _exercise_websocket_gateway_over_tcp() -> tuple[list[dict], list[object]]:
    loop = asyncio.get_running_loop()
    udp_transport, udp_protocol = await loop.create_datagram_endpoint(
        lambda: _FakeGroundfireUdpProtocol(),
        local_addr=("127.0.0.1", 0),
    )
    udp_host, udp_port = udp_transport.get_extra_info("sockname")[:2]
    fake_udp = udp_protocol
    gateway = WebSocketGateway(password="secret", udp_host=udp_host, udp_port=udp_port)
    server = await asyncio.start_server(gateway._handle_client, gateway.host, 0)
    host, port = server.sockets[0].getsockname()[:2]
    reader, writer = await asyncio.open_connection(host, port)
    try:
        await _send_websocket_handshake(reader, writer, host, port)
        messages = []
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
        return messages, list(fake_udp.messages)
    finally:
        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()
        udp_transport.close()


def _snapshot_envelope(
    player_name: str,
    *,
    snapshot_sequence: int,
    acknowledged_command_sequence: int = 0,
    terrain_patches: tuple[TerrainPatch, ...] = (),
    events: tuple[dict[str, object], ...] = (),
) -> ServerSnapshotEnvelope:
    snapshot = MatchSnapshot(
        authority="server",
        game_phase="online",
        current_round=1,
        num_rounds=10,
        simulation_tick=snapshot_sequence,
        players=(
            ReplicatedPlayerState(
                player_number=1,
                name=player_name,
                connected=True,
                tank_entity_id=7,
                acknowledged_command_sequence=acknowledged_command_sequence,
                acknowledged_snapshot_sequence=snapshot_sequence,
            ),
        ),
        entities=(
            ReplicatedEntityState(
                entity_id=7,
                entity_type="tank",
                position=(-4.0 + snapshot_sequence, 3.0),
                owner_player=1,
                payload={"health": 100},
            ),
        ),
        seed=1,
        world_width=20.0,
        terrain_revision=snapshot_sequence,
        terrain_profile=(1.0, 1.5, 2.0),
    )
    return ServerSnapshotEnvelope(
        session_id="test-session",
        snapshot_sequence=snapshot_sequence,
        simulation_tick=snapshot_sequence,
        acknowledged_command_sequences={1: acknowledged_command_sequence},
        snapshot=snapshot,
        terrain_patches=terrain_patches,
        events=events,
    )


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
