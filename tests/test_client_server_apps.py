import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from groundfire_net.browser import ServerBook, ServerListEntry
from src.gameclock import ClockTick
from src.gameui import GameUI
from src.groundfire.app.client import ClientApp
from src.groundfire.app.server import ServerApp
from src.groundfire.network.codec import encode_message
from src.groundfire.network.messages import DisconnectNotice, JoinAccept, JoinReject, Ping, ServerSnapshotEnvelope
from src.groundfire.sim.match import MatchSnapshot
from src.groundfire.ui import LocalMenuSelection, LocalPlayerConfig


class DummyGame:
    def __init__(self):
        self.frames = 0

    def loop_once(self):
        self.frames += 1
        return self.frames < 2


class ControlsStub:
    def get_command(self, _controller, _command_id):
        return False


class InterfaceStub:
    def __init__(self):
        self.started = 0
        self.ended = 0

    def should_close(self):
        return False

    def start_draw(self):
        self.started += 1

    def end_draw(self):
        self.ended += 1


class ClockStub:
    def __init__(self):
        self.ticks = 0

    def tick(self):
        self.ticks += 1
        return ClockTick(
            now=float(self.ticks),
            raw_delta=1.0 / 30.0,
            delta=1.0 / 30.0,
            simulation_time=self.ticks * (1.0 / 30.0),
            fps=30.0,
        )


class FontStub:
    def set_shadow(self, _value):
        return None

    def set_proportional(self, _value):
        return None

    def set_orientation(self, _value):
        return None

    def set_size(self, *_args):
        return None

    def set_colour(self, _colour):
        return None

    def print_centred_at(self, *args):
        return None

    def printf(self, *args):
        return None


class GraphicsStub:
    def draw_world_polygon(self, *_args, **_kwargs):
        return None

    def draw_world_rect(self, *_args, **_kwargs):
        return None

    def draw_world_line(self, *_args, **_kwargs):
        return None

    def draw_subtexture_world_rect(self, *_args, **_kwargs):
        return None

    def draw_texture_world_rect(self, *_args, **_kwargs):
        return None

    def draw_texture_centered(self, *_args, **_kwargs):
        return None

    def draw_fullscreen_overlay(self, *_args, **_kwargs):
        return None


class ConnectedGameStub:
    def __init__(self):
        self.interface = InterfaceStub()
        self.clock = ClockStub()
        self.controls = ControlsStub()
        self.font = FontStub()
        self.ui = GameUI(font_provider=lambda: self.font)
        self.graphics = GraphicsStub()

    def get_clock(self):
        return self.clock

    def get_interface(self):
        return self.interface

    def get_controls(self):
        return self.controls

    def get_ui(self):
        return self.ui

    def get_graphics(self):
        return self.graphics


class CanonicalMenuGameStub:
    def __init__(self, settings_path: Path):
        self._settings_path = settings_path
        self.close_calls = 0

    def get_settings_path(self):
        return self._settings_path

    def close(self):
        self.close_calls += 1


class LegacyGameStub:
    GameState = type(
        "GameState",
        (),
        {
            "CONTROLLERS_MENU": "controllers_menu",
            "ROUND_STARTING": "round_starting",
        },
    )

    def __init__(self):
        self.frames = 0
        self.changed_states = []
        self.deleted_players = 0
        self.num_rounds = None
        self.added_players = []
        self.close_calls = 0

    def _change_state(self, new_state):
        self.changed_states.append(new_state)

    def delete_players(self):
        self.deleted_players += 1

    def set_num_of_rounds(self, num_rounds):
        self.num_rounds = num_rounds

    def add_player(self, controller, name, colour):
        self.added_players.append((controller, name, colour))

    def loop_once(self):
        self.frames += 1
        return self.frames < 2

    def close(self):
        self.close_calls += 1


class ClientServerAppTests(unittest.TestCase):
    def test_client_state_accepts_join_and_ignores_older_snapshots(self):
        client = ClientApp(game_factory=DummyGame)
        join = JoinAccept(session_id="session-1", player_number=1, session_token="token-1")
        client.handle_packet(encode_message(join), ("127.0.0.1", 27015))
        client.get_client_state().build_command_envelope(
            {"fire": True},
            issued_at=1.0,
            source="test",
            simulation_tick=0,
        )

        baseline = self._build_snapshot(sequence=1, snapshot_kind="full", baseline_snapshot_sequence=1)
        newer = self._build_snapshot(sequence=2)
        older = self._build_snapshot(sequence=1)

        self.assertTrue(client.apply_snapshot_envelope(baseline))
        self.assertTrue(client.apply_snapshot_envelope(newer))
        self.assertFalse(client.apply_snapshot_envelope(older))
        self.assertEqual(client.get_client_state().latest_snapshot_sequence, 2)
        self.assertEqual(client.get_client_state().latest_snapshot_kind, "delta")
        self.assertEqual(client.get_client_state().latest_baseline_snapshot_sequence, 1)
        self.assertEqual(client.get_client_state().get_pending_commands(), ())

    def test_server_handles_join_and_ping_without_open_socket(self):
        server = ServerApp(enable_discovery=False)

        hello_responses = server.handle_message(Ping(nonce="123", issued_at=1.5), ("127.0.0.1", 5000))
        self.assertEqual(hello_responses[0].nonce, "123")

    def test_client_tracks_join_reject_reason(self):
        client = ClientApp(game_factory=DummyGame)

        client.handle_packet(
            encode_message(JoinReject(reason="server_full", session_id="session-1")),
            ("127.0.0.1", 27015),
        )

        self.assertEqual(client.get_client_state().join_reject_reason, "server_full")

    def test_legacy_backend_name_is_normalized_to_native_udp(self):
        client = ClientApp(
            game_factory=DummyGame,
            network_backend="legacy-external",
            secure_server_public_key_path="keys/server_root_public.pem",
        )
        try:
            sent = client.connect("127.0.0.1", 27015, player_name="Alice", requested_slot=2)

            self.assertEqual([type(message).__name__ for message in sent], ["HelloRequest", "JoinRequest"])
            self.assertEqual(client._network_backend, "udp")
        finally:
            client.close()

    def test_loopback_smoke_server_and_client_exchange_join_and_snapshot(self):
        server = ServerApp(host="127.0.0.1", port=0, discovery_port=0, enable_discovery=False)
        client = ClientApp(game_factory=DummyGame)
        try:
            server.open()
            port = server.get_bound_port()
            client.connect("127.0.0.1", port, player_name="Alice")

            deadline = time.monotonic() + 1.5
            while time.monotonic() < deadline:
                server.poll_network(timeout=0.01)
                server.step()
                client.poll_network(timeout=0.01)
                if client.get_client_state().latest_snapshot_sequence > 0:
                    break

            self.assertEqual(client.get_client_state().player_number, 0)
            self.assertGreater(client.get_client_state().latest_snapshot_sequence, 0)
            frame = client.build_remote_render_frame()
            self.assertTrue(frame.terrain_primitives)
            self.assertTrue(frame.entity_states)
            self.assertTrue(frame.hud_primitives)
            self.assertEqual(frame.metadata["local_player_number"], 0)
        finally:
            client.close()
            server.close()

    def test_local_mode_runs_canonical_loopback_path(self):
        client = ClientApp(game_factory=ConnectedGameStub)

        try:
            exit_code = client.run_local(max_frames=2, player_name="Alice", ai_players=1)

            self.assertEqual(exit_code, 0)
            self.assertEqual(client.get_client_state().player_number, 0)
            self.assertGreater(client.get_client_state().latest_snapshot_sequence, 0)
            self.assertEqual(client.get_client_state().latest_snapshot.players[0].name, "Alice")
        finally:
            client.close()

    def test_local_menu_can_switch_to_classic_and_persist_preference(self):
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "options.ini"
            settings_path.write_text("[Graphics]\nShowFPS=0\n", encoding="utf-8")
            canonical_game = CanonicalMenuGameStub(settings_path)

            class LocalRuntimeStub:
                def open_menu(self, _game, *, player_name, ai_players=1, max_frames=None):
                    return LocalMenuSelection("classic", ai_players + 1)

                def run(self, *_args, **_kwargs):
                    raise AssertionError("Canonical local runtime should not start after selecting classic menus.")

            client = ClientApp(
                game_factory=lambda: canonical_game,
                legacy_game_factory=DummyGame,
                local_runtime=LocalRuntimeStub(),
            )
            try:
                exit_code = client.run_local(show_menu=True, max_frames=2, player_name="Alice", ai_players=1)

                self.assertEqual(exit_code, 0)
                self.assertEqual(canonical_game.close_calls, 1)
                self.assertEqual(client.get_legacy_game().frames, 2)
                settings_text = settings_path.read_text(encoding="utf-8")
                self.assertIn("[Interface]", settings_text)
                self.assertIn("LocalMenuMode=classic", settings_text)
            finally:
                client.close()

    def test_local_menu_set_controls_opens_legacy_controller_menu_without_persisting_preference(self):
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "options.ini"
            settings_path.write_text("[Graphics]\nShowFPS=0\n", encoding="utf-8")
            canonical_game = CanonicalMenuGameStub(settings_path)
            legacy_game = LegacyGameStub()

            class LocalRuntimeStub:
                def open_menu(self, _game, *, player_name, ai_players=1, max_frames=None):
                    return LocalMenuSelection(
                        "classic",
                        ai_players,
                        players=(),
                        launch_target="controllers",
                        persist_mode=False,
                    )

                def run(self, *_args, **_kwargs):
                    raise AssertionError(
                        "Canonical local runtime should not start after Set Controls routes to legacy."
                    )

            client = ClientApp(
                game_factory=lambda: canonical_game,
                legacy_game_factory=lambda: legacy_game,
                local_runtime=LocalRuntimeStub(),
            )
            try:
                exit_code = client.run_local(show_menu=True, max_frames=2, player_name="Alice", ai_players=1)

                self.assertEqual(exit_code, 0)
                self.assertEqual(canonical_game.close_calls, 1)
                self.assertEqual(legacy_game.changed_states, [legacy_game.GameState.CONTROLLERS_MENU])
                settings_text = settings_path.read_text(encoding="utf-8")
                self.assertNotIn("LocalMenuMode=classic", settings_text)
            finally:
                client.close()

    def test_local_menu_start_passes_ai_players_and_num_rounds_to_modern_runtime(self):
        calls = []

        class LocalRuntimeStub:
            def open_menu(self, _game, *, player_name, ai_players=1, max_frames=None):
                return LocalMenuSelection("start", ai_players + 2, 25, local_controller=1, requested_slot=3)

            def run(
                self,
                _client,
                _game,
                *,
                player_name,
                ai_players=1,
                num_rounds=10,
                local_controller=0,
                requested_slot=0,
                player_configs=(),
                max_frames=None,
            ):
                calls.append(
                    (
                        player_name,
                        ai_players,
                        num_rounds,
                        local_controller,
                        requested_slot,
                        player_configs,
                        max_frames,
                    )
                )
                return 44

        client = ClientApp(game_factory=DummyGame, local_runtime=LocalRuntimeStub())
        try:
            exit_code = client.run_local(show_menu=True, max_frames=2, player_name="Alice", ai_players=1)

            self.assertEqual(exit_code, 44)
            self.assertEqual(calls[0], ("Alice", 3, 25, 1, 3, (), 2))
        finally:
            client.close()

    def test_local_menu_connect_selection_starts_connected_runtime_and_defers_history_until_accept(self):
        with TemporaryDirectory() as temp_dir:
            book_path = Path(temp_dir) / "servers.json"
            entry = ServerListEntry(name="Menu Server", host="127.0.0.1", port=27015, requires_password=True)
            calls = []

            class LocalRuntimeStub:
                def open_menu(self, _game, *, player_name, ai_players=1, max_frames=None):
                    return LocalMenuSelection(
                        "connect",
                        ai_players,
                        connect_host=entry.host,
                        connect_port=entry.port,
                        connect_password="secret",
                        connect_entry=entry,
                    )

                def run(self, *_args, **_kwargs):
                    raise AssertionError("Connected browser selection should not start local gameplay.")

            class ConnectedRuntimeStub:
                def run(self, client, _game, *, max_frames=None):
                    calls.append((client._server_address, client._pending_history_entry, max_frames))
                    return 55

            client = ClientApp(
                game_factory=ConnectedGameStub,
                local_runtime=LocalRuntimeStub(),
                server_book_path=book_path,
            )
            client._front_runtime = ConnectedRuntimeStub()
            try:
                exit_code = client.run_local(show_menu=True, max_frames=2, player_name="Alice", ai_players=1)

                self.assertEqual(exit_code, 55)
                self.assertEqual(calls[0][0], ("127.0.0.1", 27015))
                self.assertEqual(calls[0][1].endpoint, entry.endpoint)
                self.assertEqual(calls[0][2], 2)
                self.assertEqual(ServerBook(book_path).get_history(), ())
            finally:
                client.close()

    def test_local_menu_multi_human_start_bootstraps_legacy_roster(self):
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "options.ini"
            settings_path.write_text("[Graphics]\nShowFPS=0\n", encoding="utf-8")
            canonical_game = CanonicalMenuGameStub(settings_path)
            legacy_game = LegacyGameStub()

            players = (
                LocalPlayerConfig(slot=0, name="Player 1", is_human=True, controller=1, colour=(10, 20, 30)),
                LocalPlayerConfig(slot=1, name="Player 2", is_human=True, controller=2, colour=(40, 50, 60)),
                LocalPlayerConfig(slot=2, name="CPU 1", is_human=False, controller=7, colour=(70, 80, 90)),
            )

            class LocalRuntimeStub:
                def open_menu(self, _game, *, player_name, ai_players=1, max_frames=None):
                    return LocalMenuSelection(
                        "classic",
                        ai_players=1,
                        num_rounds=25,
                        players=players,
                        launch_target="configured_start",
                        persist_mode=False,
                    )

                def run(self, *_args, **_kwargs):
                    raise AssertionError("Canonical local runtime should not start after multi-human legacy handoff.")

            client = ClientApp(
                game_factory=lambda: canonical_game,
                legacy_game_factory=lambda: legacy_game,
                local_runtime=LocalRuntimeStub(),
            )
            try:
                exit_code = client.run_local(show_menu=True, max_frames=2, player_name="Alice", ai_players=1)

                self.assertEqual(exit_code, 0)
                self.assertEqual(canonical_game.close_calls, 1)
                self.assertEqual(legacy_game.deleted_players, 1)
                self.assertEqual(legacy_game.num_rounds, 25)
                self.assertEqual(
                    legacy_game.added_players,
                    [
                        (1, "Alice", (10, 20, 30)),
                        (2, "Player 2", (40, 50, 60)),
                        (-1, "CPU 1", (70, 80, 90)),
                    ],
                )
                self.assertEqual(legacy_game.changed_states, [legacy_game.GameState.ROUND_STARTING])
                settings_text = settings_path.read_text(encoding="utf-8")
                self.assertNotIn("LocalMenuMode=classic", settings_text)
            finally:
                client.close()

    def test_legacy_local_mode_keeps_classic_loop_path_available(self):
        client = ClientApp(game_factory=DummyGame)
        try:
            exit_code = client.run_legacy_local(max_frames=2)

            self.assertEqual(exit_code, 0)
            self.assertEqual(client.get_legacy_game().frames, 2)
        finally:
            client.close()

    def test_loopback_smoke_with_two_clients_receiving_snapshots(self):
        server = ServerApp(host="127.0.0.1", port=0, discovery_port=0, enable_discovery=False)
        alice = ClientApp(game_factory=DummyGame)
        bob = ClientApp(game_factory=DummyGame)
        try:
            server.open()
            port = server.get_bound_port()
            alice.connect("127.0.0.1", port, player_name="Alice")
            bob.connect("127.0.0.1", port, player_name="Bob")

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                server.poll_network(timeout=0.01)
                server.step()
                alice.poll_network(timeout=0.01)
                bob.poll_network(timeout=0.01)
                if (
                    alice.get_client_state().latest_snapshot_sequence > 0
                    and bob.get_client_state().latest_snapshot_sequence > 0
                ):
                    break

            self.assertEqual(alice.get_client_state().player_number, 0)
            self.assertEqual(bob.get_client_state().player_number, 1)
            self.assertGreater(alice.get_client_state().latest_snapshot_sequence, 0)
            self.assertGreater(bob.get_client_state().latest_snapshot_sequence, 0)
        finally:
            alice.close()
            bob.close()
            server.close()

    def test_client_prediction_reconciles_local_tank_after_delta_snapshot(self):
        client = ClientApp(game_factory=DummyGame)
        join = JoinAccept(session_id="session-1", player_number=0, session_token="token-1")
        client.handle_packet(encode_message(join), ("127.0.0.1", 27015))

        baseline = ServerSnapshotEnvelope(
            session_id="session-1",
            snapshot_sequence=1,
            simulation_tick=1,
            acknowledged_command_sequences={0: 0},
            snapshot=MatchSnapshot(
                authority="server",
                game_phase="round_in_action",
                current_round=1,
                num_rounds=5,
                simulation_tick=1,
                phase_ticks_remaining=120,
                players=(
                    self._player_state(
                        player_number=0,
                        tank_entity_id=10,
                        selected_weapon="missile",
                        weapon_stocks=(("missile", 1),),
                    ),
                ),
                entities=(
                    self._tank_state(entity_id=10, x=0.0, y=1.0, gun_angle=45.0, selected_weapon="missile"),
                ),
            ),
            snapshot_kind="full",
            baseline_snapshot_sequence=1,
        )
        self.assertTrue(client.apply_snapshot_envelope(baseline))

        client.get_client_state().build_command_envelope(
            {"tankright": True, "gunup": True, "fire": True},
            issued_at=2.0,
            source="test",
            simulation_tick=1,
        )
        predicted = client.get_client_state().get_render_snapshot()
        predicted_tank = predicted.entities[0]
        predicted_player = predicted.players[0]
        self.assertGreater(predicted_tank.position[0], 0.0)
        self.assertGreater(predicted_tank.payload["gun_angle"], 45.0)
        self.assertEqual(predicted_player.selected_weapon, "shell")

        delta = ServerSnapshotEnvelope(
            session_id="session-1",
            snapshot_sequence=2,
            simulation_tick=2,
            acknowledged_command_sequences={0: 1},
            snapshot=MatchSnapshot(
                authority="server",
                game_phase="round_in_action",
                current_round=1,
                num_rounds=5,
                simulation_tick=2,
                phase_ticks_remaining=119,
                players=(
                    self._player_state(
                        player_number=0,
                        tank_entity_id=10,
                        selected_weapon="shell",
                        weapon_stocks=(("missile", 0),),
                    ),
                ),
                entities=(
                    self._tank_state(entity_id=10, x=0.15, y=1.0, gun_angle=48.0, selected_weapon="shell"),
                ),
            ),
            snapshot_kind="delta",
            baseline_snapshot_sequence=1,
        )
        self.assertTrue(client.apply_snapshot_envelope(delta))
        self.assertEqual(client.get_client_state().get_pending_commands(), ())
        reconciled = client.get_client_state().get_render_snapshot()
        self.assertEqual(reconciled.entities[0].position[0], 0.15)
        self.assertEqual(reconciled.players[0].selected_weapon, "shell")

    def test_connected_run_uses_front_runtime_and_render_path(self):
        client = ClientApp(game_factory=DummyGame)

        called = []

        class FrontRuntimeStub:
            def run(self, app, game, *, max_frames=None):
                called.append((app, game, max_frames))
                return 77

        client._front_runtime = FrontRuntimeStub()

        result = client.run_connected(max_frames=3)

        self.assertEqual(result, 77)
        self.assertIs(called[0][0], client)
        self.assertEqual(called[0][2], 3)

    def test_apply_disconnect_clears_client_session_identifiers(self):
        client = ClientApp(game_factory=DummyGame)
        client.get_client_state().apply_join_accept(
            JoinAccept(session_id="session-1", player_number=4, session_token="token-4")
        )

        client.get_client_state().apply_disconnect(
            DisconnectNotice(
                session_id="session-1",
                player_number=4,
                session_token="token-4",
                reason="server_shutdown",
            )
        )

        self.assertIsNone(client.get_client_state().session_id)
        self.assertIsNone(client.get_client_state().player_number)
        self.assertEqual(client.get_client_state().disconnect_reason, "server_shutdown")

    def _build_snapshot(
        self,
        *,
        sequence: int,
        snapshot_kind: str = "delta",
        baseline_snapshot_sequence: int | None = 1,
    ) -> ServerSnapshotEnvelope:
        snapshot = MatchSnapshot(
            authority="server",
            game_phase="round_in_action",
            current_round=1,
            num_rounds=10,
            simulation_tick=sequence,
            phase_ticks_remaining=50,
            players=(),
            entities=(),
        )
        return ServerSnapshotEnvelope(
            session_id="session-1",
            snapshot_sequence=sequence,
            simulation_tick=sequence,
            acknowledged_command_sequences={1: 1},
            snapshot=snapshot,
            terrain_patches=(),
            events=(),
            snapshot_kind=snapshot_kind,
            baseline_snapshot_sequence=baseline_snapshot_sequence,
        )

    def _player_state(self, *, player_number: int, tank_entity_id: int, selected_weapon="shell", weapon_stocks=()):
        from src.groundfire.sim.match import ReplicatedPlayerState

        return ReplicatedPlayerState(
            player_number=player_number,
            name="Alice",
            tank_entity_id=tank_entity_id,
            selected_weapon=selected_weapon,
            weapon_stocks=weapon_stocks,
        )

    def _tank_state(self, *, entity_id: int, x: float, y: float, gun_angle: float, selected_weapon="shell"):
        from src.groundfire.sim.world import ReplicatedEntityState

        return ReplicatedEntityState(
            entity_id=entity_id,
            entity_type="tank",
            position=(x, y),
            owner_player=0,
            payload={
                "health": 100.0,
                "fuel": 1.0,
                "alive": True,
                "gun_angle": gun_angle,
                "size": 0.25,
                "selected_weapon": selected_weapon,
            },
        )


if __name__ == "__main__":
    unittest.main()
