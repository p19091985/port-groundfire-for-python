import unittest
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from groundfire_net import JsonDataclassCodec, ServerBook, ServerListEntry
from groundfire_net.websocket_gateway import GatewaySimulation, WebSocketGatewaySession


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
        joined = session.handle_text('{"type":"join","player_name":"GodotPlayer","password":""}')
        input_response = session.handle_text(
            '{"type":"input","sequence":7,"command":{"fire":true,"aim_left":false}}'
        )
        pong = session.handle_text('{"type":"ping","sequence":8,"client_time_msec":1234}')

        self.assertEqual(hello[0]["type"], "hello")
        self.assertEqual(joined[0]["type"], "snapshot")
        self.assertEqual(joined[0]["state"]["player_name"], "GodotPlayer")
        self.assertEqual(joined[0]["state"]["match_snapshot"]["players"][0]["name"], "GodotPlayer")
        self.assertEqual(joined[0]["state"]["match_snapshot"]["entities"][0]["entity_type"], "tank")
        self.assertEqual(input_response[0]["sequence"], 7)
        self.assertEqual(input_response[0]["state"]["last_input"]["fire"], True)
        self.assertEqual(input_response[0]["state"]["match_snapshot"]["simulation_tick"], 1)
        self.assertEqual(pong[0]["type"], "pong")
        self.assertEqual(pong[0]["client_time_msec"], 1234)

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
        self.assertEqual(fired["state"]["events"][0]["event_type"], "terrain_explosion")

    def test_websocket_gateway_session_reports_bad_messages(self):
        session = WebSocketGatewaySession()

        self.assertEqual(session.handle_text("not-json")[0]["message"], "invalid_json")
        self.assertEqual(session.handle_text('{"type":"wat"}')[0]["received_type"], "wat")


if __name__ == "__main__":
    unittest.main()
