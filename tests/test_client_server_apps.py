from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest

from src.gameclock import ClockTick
from src.gameui import GameUI
from src.groundfire.app.client import ClientApp
from src.groundfire.app.server import ServerApp
from src.groundfire.gameplay.constants import TANK_MOVE_STEP
from src.groundfire.network.codec import encode_message
from src.groundfire.network.messages import (
    DisconnectNotice,
    HelloRequest,
    JoinAccept,
    JoinReject,
    JoinRequest,
    Ping,
    RconCommand,
    RconResponse,
    ServerSnapshotEnvelope,
)
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


class LegacyGameStub:
    GameState = type(
        "GameState",
        (),
        {
            "CURRENT_STATE": "current_state",
            "MAIN_MENU": "main_menu",
            "CONTROLLERS_MENU": "controllers_menu",
            "ROUND_STARTING": "round_starting",
        },
    )

    def __init__(self):
        self.frames = 0
        self._game_state = self.GameState.MAIN_MENU
        self._new_state = self.GameState.MAIN_MENU
        self.changed_states = []
        self.deleted_players = 0
        self.num_rounds = None
        self.added_players = []
        self.close_calls = 0

    def _change_state(self, new_state):
        self.changed_states.append(new_state)
        self._game_state = new_state

    def delete_players(self):
        self.deleted_players += 1

    def set_num_of_rounds(self, num_rounds):
        self.num_rounds = num_rounds

    def add_player(self, controller, name, colour):
        self.added_players.append((controller, name, colour))

    def loop_once(self):
        self.frames += 1
        if self._new_state != self.GameState.CURRENT_STATE and self._new_state != self._game_state:
            self._change_state(self._new_state)
        return self.frames < 2

    def close(self):
        self.close_calls += 1


class OnlineConnectLegacyGameStub(LegacyGameStub):
    def __init__(self, request):
        super().__init__()
        self._request = request
        self.interface = InterfaceStub()
        self.mouse_calls = []

    def loop_once(self):
        self.frames += 1
        return True

    def consume_online_connect_request(self):
        request = self._request
        self._request = None
        return request

    def get_interface(self):
        return self

    def enable_mouse(self, enabled):
        self.mouse_calls.append(enabled)

    def should_close(self):
        return False


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

    def test_server_can_configure_match_round_count(self):
        server = ServerApp(enable_discovery=False, num_rounds=20)

        self.assertEqual(server.get_match_controller().match_state.num_rounds, 20)

    def test_server_loads_ai_special_weapon_policy_from_options(self):
        with TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "options.ini"
            settings_path.write_text(
                "[AI]\nBuySpecialWeapons=1\nUseSpecialWeapons=1\n",
                encoding="utf-8",
            )

            server = ServerApp(enable_discovery=False, settings_path=settings_path)

        ai_config = server.get_match_controller()._ai_config
        self.assertTrue(ai_config.buy_special_weapons)
        self.assertTrue(ai_config.use_special_weapons)

    def test_server_handles_basic_rcon_status_queries(self):
        server = ServerApp(
            enable_discovery=False,
            server_name="Groundfire Dedicated",
            map_seed=11,
            max_players=12,
            num_rounds=20,
            rcon_password="admin",
            region="sa",
        )

        responses = server.handle_packet(
            encode_message(RconCommand(command="status", password="admin", request_id="r1")),
            ("127.0.0.1", 5000),
        )

        self.assertIsInstance(responses[0], RconResponse)
        self.assertTrue(responses[0].ok)
        self.assertIn("name=Groundfire Dedicated", responses[0].output)
        self.assertIn("players=0/12", responses[0].output)
        self.assertIn("phase=lobby", responses[0].output)
        self.assertIn("map=seed 11", responses[0].output)
        self.assertIn("round=0/20", responses[0].output)

        rejected = server.handle_message(
            RconCommand(command="status", password="wrong", request_id="r2"),
            ("127.0.0.1", 5000),
        )
        self.assertFalse(rejected[0].ok)
        self.assertEqual(rejected[0].output, "bad_rcon_password")

    def test_server_event_logger_records_join_rcon_and_match_events(self):
        events = []
        server = ServerApp(enable_discovery=False, rcon_password="admin", event_logger=events.append)

        server.handle_message(HelloRequest(player_name="Alice"), ("127.0.0.1", 5001))
        server.handle_message(JoinRequest(player_name="Alice"), ("127.0.0.1", 5001))
        server.handle_message(RconCommand(command="status", password="wrong", request_id="bad"), ("127.0.0.1", 5000))
        server.handle_message(
            RconCommand(command="iniciar_partida", password="admin", request_id="start"),
            ("127.0.0.1", 5000),
        )
        for _ in range(server.get_match_controller().snapshot_interval_ticks + 1):
            server.step()

        self.assertTrue(any(event.startswith("server_config") for event in events))
        self.assertTrue(any(event.startswith("hello_request") for event in events))
        self.assertTrue(any(event.startswith("join_request") for event in events))
        self.assertTrue(any(event.startswith("join_accept") for event in events))
        self.assertTrue(any("reason=bad_rcon_password" in event for event in events))
        self.assertTrue(any(event.startswith("rcon_start accepted") for event in events))
        self.assertTrue(any("match_event event_type=player_joined" in event for event in events))
        self.assertTrue(any("match_event event_type=match_started" in event for event in events))
        self.assertTrue(any("match_event event_type=round_started" in event for event in events))

    def test_server_rcon_can_start_lobby_match(self):
        server = ServerApp(enable_discovery=False, rcon_password="admin")
        server.handle_message(JoinRequest(player_name="Alice"), ("127.0.0.1", 5001))

        response = server.handle_message(
            RconCommand(command="iniciar_partida", password="admin", request_id="start-1"),
            ("127.0.0.1", 5000),
        )[0]

        self.assertTrue(response.ok)
        self.assertIn("match_started", response.output)
        self.assertEqual(server.get_match_controller().match_state.game_phase, "round_starting")

    def test_server_accepts_computer_join_request_and_runs_ai(self):
        server = ServerApp(enable_discovery=False)
        controller = server.get_match_controller()

        responses = server.handle_message(
            JoinRequest(player_name="CPU LAN 1", is_computer=True),
            ("127.0.0.1", 5001),
        )
        server.handle_message(JoinRequest(player_name="Alice"), ("127.0.0.1", 5002))
        controller.start_match(reason="test")

        self.assertIsInstance(responses[0], JoinAccept)
        cpu_player = controller.match_state.get_player(responses[0].player_number)
        self.assertTrue(cpu_player.is_computer)

        for _ in range(controller.ROUND_STARTING_TICKS + 12):
            server.step()

        updated_cpu = controller.match_state.get_player(responses[0].player_number)
        self.assertGreater(updated_cpu.acknowledged_command_sequence, 0)

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

    def test_computer_client_join_request_marks_network_join(self):
        client = ClientApp(game_factory=DummyGame)
        try:
            sent = client.connect("127.0.0.1", 27015, player_name="CPU LAN 1", is_computer=True)

            self.assertEqual(type(sent[1]).__name__, "JoinRequest")
            self.assertTrue(sent[1].is_computer)
        finally:
            client.close()

    def test_headless_connected_mode_finishes_after_join_without_creating_game_window(self):
        events = []

        def fail_game_factory():
            raise AssertionError("Headless client should not create a Pygame game shell.")

        client = ClientApp(game_factory=fail_game_factory, event_logger=events.append)
        try:
            client.handle_packet(
                encode_message(JoinAccept(session_id="session-1", player_number=2, session_token="token-2")),
                ("127.0.0.1", 27015),
            )

            result = client.run_headless_connected(join_timeout=0.01)

            self.assertEqual(result, 0)
            self.assertTrue(any(event.startswith("join_accept") for event in events))
            self.assertIn("headless_complete", events)
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
            self.assertEqual(client.get_client_state().latest_snapshot.game_phase, "lobby")
            frame = client.build_remote_render_frame()
            self.assertTrue(frame.terrain_primitives)
            self.assertFalse(frame.entity_states)
            self.assertFalse(frame.hud_primitives)
            self.assertEqual(frame.metadata["local_player_number"], 0)
        finally:
            client.close()
            server.close()

    def test_local_mode_delegates_to_classic_legacy_path(self):
        events = []
        client = ClientApp(game_factory=DummyGame, event_logger=events.append)

        try:
            exit_code = client.run_local(
                show_menu=True,
                max_frames=2,
                player_name="Alice",
                ai_players=8,
                num_rounds=25,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(client.get_legacy_game().frames, 2)
            self.assertTrue(any("local_classic_only" in event for event in events))
            self.assertTrue(any("legacy_local_start" in event for event in events))
            self.assertEqual(client.get_client_state().latest_snapshot_sequence, 0)
        finally:
            client.close()

    def test_legacy_local_can_open_controller_menu_from_classic_selection(self):
        legacy_game = LegacyGameStub()
        selection = LocalMenuSelection(
            "classic",
            ai_players=1,
            players=(),
            launch_target="controllers",
            persist_mode=False,
        )
        client = ClientApp(legacy_game_factory=lambda: legacy_game)
        try:
            exit_code = client.run_legacy_local(
                max_frames=2,
                player_name="Alice",
                menu_selection=selection,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(legacy_game.changed_states, [legacy_game.GameState.CONTROLLERS_MENU])
        finally:
            client.close()

    def test_legacy_local_multi_human_start_bootstraps_classic_roster(self):
        legacy_game = LegacyGameStub()
        events = []
        players = (
            LocalPlayerConfig(slot=0, name="Player 1", is_human=True, controller=1, colour=(10, 20, 30)),
            LocalPlayerConfig(slot=1, name="Player 2", is_human=True, controller=2, colour=(40, 50, 60)),
            LocalPlayerConfig(slot=2, name="CPU 1", is_human=False, controller=7, colour=(70, 80, 90)),
        )
        selection = LocalMenuSelection(
            "classic",
            ai_players=1,
            num_rounds=25,
            players=players,
            launch_target="configured_start",
            persist_mode=False,
        )

        client = ClientApp(
            legacy_game_factory=lambda: legacy_game,
            event_logger=events.append,
        )
        try:
            exit_code = client.run_legacy_local(
                max_frames=2,
                player_name="Alice",
                menu_selection=selection,
            )

            self.assertEqual(exit_code, 0)
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
            self.assertEqual(legacy_game._game_state, legacy_game.GameState.ROUND_STARTING)
            self.assertEqual(legacy_game._new_state, legacy_game.GameState.ROUND_STARTING)
            self.assertTrue(any("legacy_config target=configured_start" in event for event in events))
            self.assertTrue(any("legacy_state_change" in event for event in events))
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

    def test_legacy_local_server_browser_connects_with_classic_game_window(self):
        events = []
        request = {
            "host": "127.0.0.1",
            "port": 27015,
            "password": "secret",
            "entry": None,
            "is_computer": True,
        }
        legacy_game = OnlineConnectLegacyGameStub(request)
        client = ClientApp(
            legacy_game_factory=lambda: legacy_game,
            event_logger=events.append,
        )
        calls = []

        class FrontRuntimeStub:
            def run(self, app, game, *, max_frames=None, **kwargs):
                calls.append((app, game, max_frames, kwargs))
                return 0

        client._front_runtime = FrontRuntimeStub()
        try:
            exit_code = client.run_legacy_local(max_frames=3, player_name="Alice")

            self.assertEqual(exit_code, 0)
            self.assertEqual(legacy_game.frames, 1)
            self.assertEqual(legacy_game.mouse_calls, [False])
            self.assertEqual(client._server_address, ("127.0.0.1", 27015))
            self.assertIs(calls[0][1], legacy_game)
            self.assertEqual(calls[0][2], 2)
            self.assertFalse(calls[0][3]["send_local_commands"])
            self.assertTrue(client._connected_computer_player)
            self.assertTrue(
                any("legacy_local_connect host=127.0.0.1 port=27015 computer=true" in event for event in events)
            )
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

    def test_loopback_smoke_with_six_headless_computer_clients(self):
        server = ServerApp(host="127.0.0.1", port=0, discovery_port=0, enable_discovery=False)
        clients = [ClientApp(game_factory=DummyGame) for _ in range(6)]
        try:
            server.open()
            port = server.get_bound_port()
            for index, client in enumerate(clients, start=1):
                client.connect("127.0.0.1", port, player_name=f"CPU Auto {index}", is_computer=True)

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                server.poll_network(timeout=0.01)
                server.step()
                for client in clients:
                    client.poll_network(timeout=0.0)
                if all(client.get_client_state().session_id for client in clients):
                    break

            self.assertEqual(len(server.get_match_controller().match_state.player_slots), 6)
            self.assertTrue(
                all(player.is_computer for player in server.get_match_controller().match_state.player_slots.values())
            )
        finally:
            for client in clients:
                client.close()
            server.close()

    def test_client_close_sends_disconnect_notice_and_frees_server_slot(self):
        server = ServerApp(host="127.0.0.1", port=0, discovery_port=0, enable_discovery=False)
        client = ClientApp(game_factory=DummyGame)
        try:
            server.open()
            client.connect("127.0.0.1", server.get_bound_port(), player_name="Alice")

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                server.poll_network(timeout=0.01)
                client.poll_network(timeout=0.01)
                if client.get_client_state().session_id is not None:
                    break

            self.assertEqual(len(server.get_match_controller().match_state.player_slots), 1)

            client.close()

            deadline = time.monotonic() + 2.0
            while time.monotonic() < deadline:
                server.poll_network(timeout=0.01)
                if not server.get_match_controller().match_state.player_slots:
                    break

            self.assertEqual(server.get_match_controller().match_state.player_slots, {})
        finally:
            client.close()
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
                    self._tank_state(entity_id=10, x=TANK_MOVE_STEP, y=1.0, gun_angle=48.0, selected_weapon="shell"),
                ),
            ),
            snapshot_kind="delta",
            baseline_snapshot_sequence=1,
        )
        self.assertTrue(client.apply_snapshot_envelope(delta))
        self.assertEqual(client.get_client_state().get_pending_commands(), ())
        reconciled = client.get_client_state().get_render_snapshot()
        self.assertEqual(reconciled.entities[0].position[0], TANK_MOVE_STEP)
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

    def test_connected_computer_client_suppresses_local_keyboard_commands(self):
        client = ClientApp(game_factory=DummyGame)
        client._connected_computer_player = True
        called = []

        class FrontRuntimeStub:
            def run(self, app, game, *, max_frames=None, send_local_commands=True):
                called.append((app, game, max_frames, send_local_commands))
                return 78

        client._front_runtime = FrontRuntimeStub()

        result = client.run_connected(max_frames=3)

        self.assertEqual(result, 78)
        self.assertIs(called[0][0], client)
        self.assertEqual(called[0][2], 3)
        self.assertFalse(called[0][3])

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
