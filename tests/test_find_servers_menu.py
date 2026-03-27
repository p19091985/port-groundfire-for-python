import types
import unittest
from unittest.mock import patch

from tests.support import install_fake_pygame

install_fake_pygame()

import pygame

from src.common import GameState
from src.findserversmenu import FindServersMenu
from src.mainmenu import MainMenu


class DummyFont:
    def __init__(self):
        self.calls = []

    def set_colour(self, *_args):
        return None

    def set_shadow(self, *_args):
        return None

    def set_size(self, *_args):
        return None

    def find_string_length(self, text):
        return max(1, len(text))

    def print_centred_at(self, *_args):
        self.calls.append(("print_centred_at", _args))


class DummyInterface:
    def __init__(self):
        self._window = pygame.Surface((1024, 768))
        self.mouse_enabled = False

    def get_window_settings(self):
        return (1024, 768, False)

    def enable_mouse(self, enable):
        self.mouse_enabled = enable

    def offset_viewport(self, _x, _y):
        return None

    def get_texture_image(self, _texture_id):
        return pygame.Surface((64, 64))

    def game_to_screen(self, x, y):
        return (int((x + 10.0) * 10), int((7.5 - y) * 10))


class DummyGame:
    def __init__(self):
        self._interface = DummyInterface()
        self._font = DummyFont()
        self._settings = types.SimpleNamespace(
            get_string=lambda *_args, **_kwargs: "Player",
            get_int=lambda *_args, **_kwargs: 0,
        )
        self.prepared_match = None

    def get_interface(self):
        return self._interface

    def get_font(self):
        return self._font

    def get_settings(self):
        return self._settings

    def prepare_online_match(self, match_setup):
        self.prepared_match = match_setup


class FakeClientInterface:
    def __init__(self, width, height, _settings=None):
        self.size = (width, height)
        self.updated = []
        self.draw_calls = 0
        self.next_action = None
        self.match_setup = None

    def update(self, dt):
        self.updated.append(dt)

    def handle_event(self, _event):
        action = self.next_action
        self.next_action = None
        return action

    def draw_to_interface(self, _interface):
        self.draw_calls += 1

    def shutdown(self):
        return None

    def consume_match_setup(self):
        match_setup = self.match_setup
        self.match_setup = None
        return match_setup


class MainAndFindServersMenuTests(unittest.TestCase):
    def test_main_menu_routes_to_find_servers_state(self):
        menu = MainMenu(DummyGame())
        menu._start_button.update = lambda: False
        menu._find_servers_button.update = lambda: True
        menu._options_button.update = lambda: False
        menu._quit_button.update = lambda: False

        self.assertEqual(menu.update(0.1), GameState.FIND_SERVERS_MENU)

    def test_find_servers_menu_closes_on_escape(self):
        with patch("src.findserversmenu.NetworkClientInterface", FakeClientInterface):
            with patch.object(pygame.event, "get", return_value=[types.SimpleNamespace(type=768, key=27)]):
                menu = FindServersMenu(DummyGame())
                self.assertEqual(menu.update(0.1), GameState.MAIN_MENU)

    def test_find_servers_menu_draws_client_interface_and_handles_close_action(self):
        with patch("src.findserversmenu.NetworkClientInterface", FakeClientInterface):
            menu = FindServersMenu(DummyGame())
            menu.draw()
            self.assertEqual(menu._client_interface.draw_calls, 1)

            menu._client_interface.next_action = types.SimpleNamespace(kind="close")
            with patch.object(pygame.event, "get", return_value=[types.SimpleNamespace(type=1025, pos=(10, 10), button=1)]):
                self.assertEqual(menu.update(0.1), GameState.MAIN_MENU)

    def test_find_servers_menu_starts_online_match_when_client_launches_setup(self):
        with patch("src.findserversmenu.NetworkClientInterface", FakeClientInterface):
            game = DummyGame()
            menu = FindServersMenu(game)
            menu._client_interface.match_setup = types.SimpleNamespace(match_id="match-1")

            self.assertEqual(menu.update(0.1), GameState.ROUND_STARTING)
            self.assertEqual(game.prepared_match.match_id, "match-1")


if __name__ == "__main__":
    unittest.main()
