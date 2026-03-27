import unittest

from src.gameclock import ClockTick
from src.gameui import GameUI
from src.groundfire.app.front import ConnectedFrontRuntime, LocalCommandSampler


class ControlsStub:
    def __init__(self, states=None):
        self.states = dict(states or {})
        self.calls = []

    def get_command(self, controller, command_id):
        self.calls.append((controller, command_id))
        return self.states.get((controller, command_id), self.states.get(command_id, False))


class InterfaceStub:
    def __init__(self, should_close=False):
        self._should_close = should_close
        self.start_draw_calls = 0
        self.end_draw_calls = 0

    def should_close(self):
        return self._should_close

    def start_draw(self):
        self.start_draw_calls += 1

    def end_draw(self):
        self.end_draw_calls += 1


class FontStub:
    def __init__(self):
        self.centred_calls = []
        self.printf_calls = []

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
        self.centred_calls.append(args)

    def printf(self, *args):
        self.printf_calls.append(args)


class HudRendererStub:
    def __init__(self):
        self.fps_calls = []

    def render_fps(self, _game, fps):
        self.fps_calls.append(fps)


class ClockStub:
    def __init__(self):
        self.tick_calls = 0

    def tick(self):
        self.tick_calls += 1
        return ClockTick(
            now=float(self.tick_calls),
            raw_delta=1.0 / 60.0,
            delta=1.0 / 60.0,
            simulation_time=self.tick_calls * (1.0 / 60.0),
            fps=60.0,
        )


class GameStub:
    def __init__(self, *, command_states=None, show_fps=False):
        self.interface = InterfaceStub()
        self.controls = ControlsStub(command_states)
        self.font = FontStub()
        self.ui = GameUI(font_provider=lambda: self.font)
        self.clock = ClockStub()
        self.hud_renderer = HudRendererStub()
        self._show_fps = show_fps

    def get_controls(self):
        return self.controls

    def get_interface(self):
        return self.interface

    def get_ui(self):
        return self.ui

    def get_clock(self):
        return self.clock

    def get_hud_renderer(self):
        return self.hud_renderer


class ClientStateStub:
    def __init__(
        self,
        *,
        session_id=None,
        player_number=None,
        latest_snapshot=None,
        server_name=None,
        join_reject_reason=None,
        disconnect_reason=None,
    ):
        self.session_id = session_id
        self.player_number = player_number
        self.latest_snapshot = latest_snapshot
        self.server_name = server_name
        self.join_reject_reason = join_reject_reason
        self.disconnect_reason = disconnect_reason


class ClientStub:
    def __init__(
        self,
        *,
        session_id=None,
        player_number=None,
        latest_snapshot=None,
        server_name=None,
        join_reject_reason=None,
        disconnect_reason=None,
    ):
        self.client_state = ClientStateStub(
            session_id=session_id,
            player_number=player_number,
            latest_snapshot=latest_snapshot,
            server_name=server_name,
            join_reject_reason=join_reject_reason,
            disconnect_reason=disconnect_reason,
        )
        self.poll_calls = []
        self.sent_commands = []
        self.render_calls = 0
        self.rendered_frames = []

    def poll_network(self, *, timeout=0.0):
        self.poll_calls.append(timeout)
        return ()

    def get_client_state(self):
        return self.client_state

    def build_and_send_command_envelope(self, commands, *, source):
        self.sent_commands.append((dict(commands), source))
        return None

    def build_remote_render_frame(self):
        return type("Frame", (), {"metadata": {"game_phase": "round_in_action", "current_round": 1}})()

    def render_connected_frame(self, _game, frame=None):
        self.render_calls += 1
        self.rendered_frames.append(frame)
        return None


class ConnectedFrontTests(unittest.TestCase):
    def test_local_command_sampler_maps_controls_to_command_names(self):
        sampler = LocalCommandSampler()
        game = GameStub(command_states={0: True, 5: True, 9: True})

        commands = sampler.sample(game, controller=0)

        self.assertTrue(commands["fire"])
        self.assertTrue(commands["tankleft"])
        self.assertTrue(commands["gunup"])
        self.assertFalse(commands["weaponup"])

    def test_local_command_sampler_uses_requested_controller_index(self):
        sampler = LocalCommandSampler()
        game = GameStub(command_states={(1, 0): True, (1, 5): True})

        commands = sampler.sample(game, controller=1)

        self.assertTrue(commands["fire"])
        self.assertTrue(commands["tankleft"])
        self.assertTrue(all(controller == 1 for controller, _command in game.controls.calls))

    def test_tick_renders_remote_frame_and_sends_commands_once_joined(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub(command_states={0: True}, show_fps=True)
        client = ClientStub(session_id="session-1", player_number=0, latest_snapshot=object())
        frame = ClockTick(now=1.0, raw_delta=1.0 / 60.0, delta=1.0 / 60.0, simulation_time=1.0, fps=55.0)

        result = runtime.tick(client, game, frame=frame)

        self.assertTrue(result.rendered_remote)
        self.assertIsNone(result.overlay_text)
        self.assertEqual(client.render_calls, 1)
        self.assertEqual(result.frame_metadata["game_phase"], "round_in_action")
        self.assertEqual(client.sent_commands[0][0]["fire"], True)
        self.assertEqual(client.sent_commands[0][1], "client:keyboard0")
        self.assertEqual(game.interface.start_draw_calls, 1)
        self.assertEqual(game.interface.end_draw_calls, 1)
        self.assertEqual(game.hud_renderer.fps_calls, [55.0])

    def test_tick_routes_commands_through_keyboard2_source(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub(command_states={(1, 0): True})
        client = ClientStub(session_id="session-1", player_number=0, latest_snapshot=object())
        frame = ClockTick(now=1.0, raw_delta=1.0 / 60.0, delta=1.0 / 60.0, simulation_time=1.0, fps=60.0)

        result = runtime.tick(client, game, frame=frame, controller=1)

        self.assertTrue(result.rendered_remote)
        self.assertEqual(client.sent_commands[0][1], "client:keyboard1")
        self.assertTrue(all(controller == 1 for controller, _command in game.controls.calls))

    def test_tick_routes_commands_through_joystick_source(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub(command_states={(2, 0): True})
        client = ClientStub(session_id="session-1", player_number=0, latest_snapshot=object())
        frame = ClockTick(now=1.0, raw_delta=1.0 / 60.0, delta=1.0 / 60.0, simulation_time=1.0, fps=60.0)

        result = runtime.tick(client, game, frame=frame, controller=2)

        self.assertTrue(result.rendered_remote)
        self.assertEqual(client.sent_commands[0][1], "client:joystick1")
        self.assertTrue(all(controller == 2 for controller, _command in game.controls.calls))

    def test_tick_draws_connecting_overlay_before_snapshot(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub()
        client = ClientStub(session_id=None, player_number=None, latest_snapshot=None)
        frame = ClockTick(now=1.0, raw_delta=1.0 / 60.0, delta=1.0 / 60.0, simulation_time=1.0, fps=0.0)

        result = runtime.tick(client, game, frame=frame)

        self.assertFalse(result.rendered_remote)
        self.assertEqual(result.overlay_text, "Connecting...")
        self.assertEqual(client.render_calls, 0)
        self.assertEqual(client.sent_commands, [])
        self.assertEqual(
            game.font.centred_calls,
            [
                (0.0, 0.4, "Groundfire Online"),
                (0.0, -0.1, "Connecting..."),
            ],
        )

    def test_tick_uses_server_name_and_rejection_reason_in_overlay(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub()
        client = ClientStub(server_name="Groundfire Arena")
        frame = ClockTick(now=1.0, raw_delta=1.0 / 60.0, delta=1.0 / 60.0, simulation_time=1.0, fps=0.0)

        connecting = runtime.tick(client, game, frame=frame)
        self.assertEqual(connecting.overlay_text, "Joining Groundfire Arena...")

        rejected = ClientStub(join_reject_reason="server_full")
        rejected_result = runtime.tick(rejected, game, frame=frame)
        self.assertEqual(rejected_result.overlay_text, "Join rejected: server_full")

    def test_run_uses_game_clock_for_each_connected_frame(self):
        runtime = ConnectedFrontRuntime()
        game = GameStub()
        client = ClientStub(session_id="session-1", player_number=0, latest_snapshot=object())

        exit_code = runtime.run(client, game, max_frames=2)

        self.assertEqual(exit_code, 0)
        self.assertEqual(game.clock.tick_calls, 2)
        self.assertEqual(client.render_calls, 2)


if __name__ == "__main__":
    unittest.main()
