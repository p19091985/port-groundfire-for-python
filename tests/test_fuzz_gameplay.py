import unittest
from unittest.mock import patch

from tests.support import install_fake_pygame

install_fake_pygame()

import pygame

import src.game as game_module
import src.shopmenu as shopmenu_module
from src.common import GameState
from tests.support import DummySoundManager, FlowPlayer, FlatLandscape


class FakeInterface:
    def __init__(self, width, height, fullscreen):
        self._width = width
        self._height = height
        self._fullscreen = fullscreen
        self._mouse_enabled = False
        self._window = pygame.Surface((width, height))

    def define_textures(self, _count):
        return None

    def load_texture(self, _filename, _texture_id):
        return True

    def enable_mouse(self, enable):
        self._mouse_enabled = enable

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

    def game_to_screen(self, x, y):
        return (int(x), int(y))

    def scale_len(self, length):
        return int(length * 10)

    def get_window_settings(self):
        return (self._width, self._height, self._fullscreen)

    def get_texture_surface(self, _texture_id):
        return pygame.Surface((32, 32))

    def get_texture_image(self, _texture_id):
        return pygame.Surface((32, 32))

    def set_texture(self, _texture):
        return None


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

    def print_at(self, *_args):
        return None

    def set_orientation(self, _value):
        return None

    def set_proportional(self, _value):
        return None

    def printf(self, *_args):
        return None


class FakeSound(DummySoundManager):
    def __init__(self, _count):
        super().__init__()


class FakeControls:
    def __init__(self, _interface):
        return None


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
        return GameState.CURRENT_STATE

    def draw(self):
        return None


class FakeLandscape(FlatLandscape):
    created_count = 0

    def __init__(self, settings, seed):
        super().__init__(ground_y=0.0, width=settings.get_float("Terrain", "Width", 11.0))
        self.seed = seed
        FakeLandscape.created_count += 1


class FakeQuake:
    def __init__(self, _game):
        self.pre_round_calls = 0

    def update(self, _time):
        return True

    def draw(self):
        return None

    def do_pre_round(self):
        self.pre_round_calls += 1
        return True

    def do_post_round(self):
        return False


class GameFlowSimulationTests(unittest.TestCase):
    def setUp(self):
        FakeLandscape.created_count = 0
        self.patchers = [
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
            patch.object(game_module, "QuitMenu", FakeMenu),
            patch.object(game_module, "ControllerMenu", FakeMenu),
            patch.object(game_module, "SetControlsMenu", FakeMenu),
            patch.object(game_module, "Quake", FakeQuake),
        ]

        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

        self.game = game_module.Game()

    def _inject_players(self, scores=(0, 0)):
        players = [FlowPlayer(f"P{i+1}", score=scores[i]) for i in range(len(scores))]
        self.game._players = players + [None] * (8 - len(players))
        self.game._number_of_players = len(players)
        self.game._entity_list = [player.get_tank() for player in players]
        return players

    def _finish_single_round_match(self):
        self.game._change_state(GameState.ROUND_STARTING)
        self.game._game_state = GameState.ROUND_FINISHING
        self.game._end_round()

        self.game._change_state(GameState.ROUND_SCORE)
        score_state = self.game.get_current_menu().update(4.1)
        self.assertEqual(score_state, GameState.WINNER_MENU)

        self.game._change_state(GameState.WINNER_MENU)
        self.assertEqual(self.game.get_current_menu().update(4.1), GameState.CURRENT_STATE)
        winner_state = self.game.get_current_menu().update(0.1)
        self.assertEqual(winner_state, GameState.MAIN_MENU)

        self.game._change_state(GameState.MAIN_MENU)

    def test_round_can_finish_and_restart_cleanly(self):
        players = self._inject_players(scores=(100, 50))
        self.game.set_num_of_rounds(2)

        self.game._change_state(GameState.ROUND_STARTING)
        self.assertEqual(self.game.get_current_round(), 1)
        self.assertEqual(FakeLandscape.created_count, 1)
        self.assertEqual([player.new_round_calls for player in players], [1, 1])
        positions = sorted(tank.position_calls[0] for tank in self.game._entity_list if hasattr(tank, "position_calls"))
        self.assertEqual(positions, [-5.0, 5.0])

        self.game._game_state = GameState.ROUND_IN_ACTION
        self.game._number_of_active_tanks = 2
        self.game.record_tank_death()
        self.assertEqual(self.game._new_state, GameState.ROUND_FINISHING)
        self.assertEqual(self.game._state_countdown, 5.0)

        self.game._game_state = GameState.ROUND_FINISHING
        self.game._end_round()
        self.assertIsNone(self.game.get_landscape())
        self.assertEqual([player.end_round_calls for player in players], [1, 1])

        self.game._change_state(GameState.ROUND_SCORE)
        next_state = self.game.get_current_menu().update(4.1)
        self.assertEqual(next_state, GameState.SHOP_MENU)

        self.game._change_state(GameState.ROUND_STARTING)
        self.assertEqual(self.game.get_current_round(), 2)
        self.assertEqual(FakeLandscape.created_count, 2)
        self.assertEqual([player.new_round_calls for player in players], [2, 2])

    def test_match_can_finish_and_new_match_can_start_after_winner_menu(self):
        self._inject_players(scores=(200, 100))
        self.game.set_num_of_rounds(1)

        self._finish_single_round_match()
        self.assertEqual(self.game.get_num_of_players(), 0)
        self.assertEqual(self.game.get_current_round(), 0)
        self.assertEqual(self.game._entity_list, [])

        new_players = self._inject_players(scores=(0, 0))
        self.game._change_state(GameState.ROUND_STARTING)
        self.assertEqual(self.game.get_current_round(), 1)
        self.assertEqual([player.new_round_calls for player in new_players], [1, 1])

    def test_two_full_matches_can_run_back_to_back(self):
        first_match_players = self._inject_players(scores=(200, 100))
        self.game.set_num_of_rounds(1)

        self._finish_single_round_match()
        self.assertEqual([player.end_round_calls for player in first_match_players], [1, 1])
        self.assertEqual(self.game.get_num_of_players(), 0)
        self.assertEqual(self.game.get_current_round(), 0)
        self.assertEqual(self.game._entity_list, [])

        second_match_players = self._inject_players(scores=(50, 150))
        self.game.set_num_of_rounds(1)

        self._finish_single_round_match()
        self.assertEqual([player.end_round_calls for player in second_match_players], [1, 1])
        self.assertEqual(self.game.get_num_of_players(), 0)
        self.assertEqual(self.game.get_current_round(), 0)
        self.assertEqual(self.game._entity_list, [])
        self.assertGreaterEqual(FakeLandscape.created_count, 2)

    def test_two_ai_players_finish_shop_menu_automatically(self):
        self.game.add_player(-1, "CPU 1", (255, 0, 0))
        self.game.add_player(-1, "CPU 2", (0, 255, 0))

        menu = shopmenu_module.ShopMenu(self.game)
        self.game._current_menu = menu
        self.game._game_state = GameState.SHOP_MENU

        next_state = GameState.CURRENT_STATE
        for _ in range(6):
            next_state = menu.update(0.25)

        self.assertEqual(menu._player_select_pos[:2], [10, 10])
        self.assertEqual(menu._player_done[:2], [True, True])
        self.assertEqual(next_state, GameState.ROUND_STARTING)


if __name__ == "__main__":
    unittest.main()
