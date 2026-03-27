import unittest
from unittest.mock import patch

from tests.support import DummySoundManager, FlatLandscape, install_fake_pygame

install_fake_pygame()

import pygame

import src.game as game_module
from interface_net import NetworkConfig, NetworkSession
from interface_net.online_match import OnlineMatchPlayer, OnlineMatchSetup
from src.humanplayer import HumanPlayer


class FakeInterface:
    def __init__(self, width, height, fullscreen):
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._window = pygame.Surface((width, height))

    def define_textures(self, _count):
        return None

    def load_texture(self, _filename, _texture_id):
        return True

    def enable_mouse(self, _enable):
        return None

    def offset_viewport(self, _x, _y):
        return None

    def should_close(self):
        return False

    def start_draw(self):
        return None

    def end_draw(self):
        return None

    def get_key(self, _key):
        return False


class FakeFont:
    def __init__(self, _interface, _texture_id):
        return None

    def set_shadow(self, _value):
        return None

    def set_size(self, *_args):
        return None

    def set_colour(self, _colour):
        return None

    def print_centred_at(self, *_args):
        return None


class FakeSound(DummySoundManager):
    def __init__(self, _count):
        super().__init__()


class FakeControls:
    def __init__(self, _interface):
        self.calls = []

    def get_command(self, controller, command):
        self.calls.append((controller, command))
        return False


class FakeControlsFile:
    def __init__(self, _controls, _file_name):
        return None

    def read_file(self):
        return None

    def write_file(self):
        return None


class FakeMenu:
    def __init__(self, *_args, **_kwargs):
        return None

    def update(self, _time):
        return game_module.GameState.CURRENT_STATE

    def draw(self):
        return None


class FakeLandscape(FlatLandscape):
    def __init__(self, settings, _seed):
        super().__init__(ground_y=0.0, width=settings.get_float("Terrain", "Width", 11.0))


class RecordingNetworkSession(NetworkSession):
    def __init__(self):
        super().__init__(NetworkConfig())
        self.attached_game = None
        self.frame_events = []
        self.round_events = []
        self.online_match = None

    def attach_game(self, game):
        super().attach_game(game)
        self.attached_game = game

    def begin_frame(self, game_time, dt):
        self.frame_events.append(("begin", game_time, dt))

    def end_frame(self, game_time, dt):
        self.frame_events.append(("end", game_time, dt))

    def before_round_start(self, round_number):
        self.round_events.append(("start", round_number))

    def after_round_end(self, round_number):
        self.round_events.append(("end", round_number))

    def get_command(self, player_number, controller, command, controls):
        return controls.get_command(controller, command)

    def activate_online_match(self, match_setup):
        self.online_match = match_setup

    def clear_online_match(self):
        self.online_match = None


class StubNetworkSession:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_command(self, player_number, controller, command, controls):
        self.calls.append((player_number, controller, command, controls))
        return self.result


class DummyGame:
    def __init__(self, session):
        self._session = session

    def get_network_session(self):
        return self._session


class DummyTank:
    def __init__(self, _game, _player, _number):
        return None


class NetworkIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.recording_session = RecordingNetworkSession()
        self.patchers = [
            patch.object(game_module, "build_network_session", return_value=self.recording_session),
            patch.object(game_module, "Interface", FakeInterface),
            patch.object(game_module, "Font", FakeFont),
            patch.object(game_module, "Sound", FakeSound),
            patch.object(game_module, "Controls", FakeControls),
            patch.object(game_module, "ControlsFile", FakeControlsFile),
            patch.object(game_module, "Landscape", FakeLandscape),
            patch.object(game_module, "MainMenu", FakeMenu),
            patch.object(game_module, "PlayerMenu", FakeMenu),
            patch.object(game_module, "OptionMenu", FakeMenu),
            patch.object(game_module, "ShopMenu", FakeMenu),
            patch.object(game_module, "ScoreMenu", FakeMenu),
            patch.object(game_module, "QuitMenu", FakeMenu),
            patch.object(game_module, "WinnerMenu", FakeMenu),
            patch.object(game_module, "ControllerMenu", FakeMenu),
            patch.object(game_module, "SetControlsMenu", FakeMenu),
        ]

        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_game_consumes_network_session_from_interface_net(self):
        game = game_module.Game()

        self.assertIs(game.get_network_session(), self.recording_session)
        self.assertIs(self.recording_session.attached_game, game)

        game.loop_once()
        self.assertEqual(self.recording_session.frame_events[0][0], "begin")
        self.assertEqual(self.recording_session.frame_events[-1][0], "end")

        game.add_player(0, "Player 1", (255, 255, 255))
        self.assertIn(0, self.recording_session.get_registered_players())

        game._start_round()
        game._end_round()
        self.assertEqual(self.recording_session.round_events, [("start", 1), ("end", 1)])

        game.delete_players()
        self.assertEqual(self.recording_session.get_registered_players(), {})

    def test_human_player_reads_commands_via_network_session(self):
        controls = FakeControls(None)
        session = StubNetworkSession(True)
        start_time_ref = [1.0]

        with patch("src.player.Tank", DummyTank):
            player = HumanPlayer(DummyGame(session), 2, "Net Player", (255, 255, 255), 4, controls)

        self.assertTrue(player.get_command(7, start_time_ref))
        self.assertTrue(player.get_command(7))
        self.assertEqual(start_time_ref[0], 0.0)
        self.assertEqual(session.calls, [(2, 4, 7, controls), (2, 4, 7, controls)])
        self.assertEqual(controls.calls, [])

    def test_game_prepares_online_match_with_local_ai_and_remote_proxy(self):
        game = game_module.Game()
        match_setup = OnlineMatchSetup(
            match_id="match-123",
            host="127.0.0.1",
            port=27016,
            player_id="local-player",
            local_player_slot=0,
            rounds=15,
            landscape_seed=100,
            tank_seed=200,
            players=(
                OnlineMatchPlayer(player_number=0, name="Local AI", is_local=True, uses_ai=True),
                OnlineMatchPlayer(player_number=1, name="Remote Human", is_local=False, uses_ai=False),
            ),
        )

        with patch("src.player.Tank", DummyTank):
            game.prepare_online_match(match_setup)

        self.assertIs(self.recording_session.online_match, match_setup)
        self.assertEqual(game.get_num_of_players(), 2)
        self.assertEqual(game.get_num_of_rounds(), 15)
        self.assertTrue(game.get_players()[0].is_computer())
        self.assertFalse(game.get_players()[1].is_computer())


if __name__ == "__main__":
    unittest.main()
