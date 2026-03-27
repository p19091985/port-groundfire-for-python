import unittest

from src.common import GameState
from src.gameflow import GameFlowController


class InterfaceStub:
    def __init__(self):
        self.mouse_calls = []
        self.offset_calls = []

    def enable_mouse(self, enabled):
        self.mouse_calls.append(enabled)

    def offset_viewport(self, x, y):
        self.offset_calls.append((x, y))


class MenuStub:
    def __init__(self, next_state=GameState.CURRENT_STATE):
        self.next_state = next_state
        self.update_calls = []
        self.draw_calls = 0

    def update(self, dt):
        self.update_calls.append(dt)
        return self.next_state

    def draw(self):
        self.draw_calls += 1


class GameStub:
    def __init__(self):
        self._current_menu = None
        self._current_round = 7
        self._state_countdown = 0.0
        self._active_controller = 3
        self.deleted_players = 0
        self.started_rounds = 0
        self.interface = InterfaceStub()

    def delete_players(self):
        self.deleted_players += 1

    def get_interface(self):
        return self.interface

    def get_active_controller(self):
        return self._active_controller

    def _start_round(self):
        self.started_rounds += 1


class GameFlowControllerTests(unittest.TestCase):
    def test_update_menu_delegates_update_without_rendering(self):
        controller = GameFlowController(menu_factories={})
        game = GameStub()
        game._current_menu = MenuStub(next_state=GameState.OPTION_MENU)

        next_state = controller.update_menu(game, 0.25)

        self.assertEqual(next_state, GameState.OPTION_MENU)
        self.assertEqual(game._current_menu.update_calls, [0.25])
        self.assertEqual(game._current_menu.draw_calls, 0)

    def test_enter_state_main_menu_from_pause_cleans_and_enables_mouse(self):
        controller = GameFlowController(menu_factories={GameState.MAIN_MENU: lambda _game: "main"})
        game = GameStub()

        controller.enter_state(game, GameState.MAIN_MENU, GameState.PAUSE_MENU)

        self.assertEqual(game.deleted_players, 1)
        self.assertEqual(game._current_menu, "main")
        self.assertEqual(game.interface.mouse_calls, [True])
        self.assertEqual(game.interface.offset_calls, [(0, 0)])

    def test_enter_state_set_controls_uses_active_controller(self):
        captured = []
        controller = GameFlowController(
            menu_factories={
                GameState.SET_CONTROLS_MENU: lambda game: captured.append(game.get_active_controller()) or "controls"
            }
        )
        game = GameStub()

        controller.enter_state(game, GameState.SET_CONTROLS_MENU, GameState.CONTROLLERS_MENU)

        self.assertEqual(captured, [3])
        self.assertEqual(game._current_menu, "controls")

    def test_enter_state_quit_menu_enables_mouse_for_confirmation_clicks(self):
        controller = GameFlowController(menu_factories={GameState.QUIT_MENU: lambda _game: "quit"})
        game = GameStub()

        controller.enter_state(game, GameState.QUIT_MENU, GameState.ROUND_IN_ACTION)

        self.assertEqual(game._current_menu, "quit")
        self.assertEqual(game.interface.mouse_calls, [True])

    def test_enter_state_round_starting_clears_menu_and_starts_round(self):
        controller = GameFlowController(menu_factories={})
        game = GameStub()
        game._current_menu = "anything"

        controller.enter_state(game, GameState.ROUND_STARTING, GameState.SHOP_MENU)

        self.assertIsNone(game._current_menu)
        self.assertEqual(game.interface.mouse_calls, [False])
        self.assertEqual(game._state_countdown, 2.0)
        self.assertEqual(game.started_rounds, 1)

    def test_select_players_resets_round_counter(self):
        controller = GameFlowController(menu_factories={GameState.SELECT_PLAYERS_MENU: lambda _game: "players"})
        game = GameStub()

        controller.enter_state(game, GameState.SELECT_PLAYERS_MENU, GameState.MAIN_MENU)

        self.assertEqual(game._current_round, 0)
        self.assertEqual(game._current_menu, "players")

    def test_round_state_helper_identifies_round_states(self):
        controller = GameFlowController(menu_factories={})

        self.assertTrue(controller.is_round_state(GameState.ROUND_STARTING))
        self.assertTrue(controller.is_round_state(GameState.ROUND_IN_ACTION))
        self.assertTrue(controller.is_round_state(GameState.ROUND_FINISHING))
        self.assertFalse(controller.is_round_state(GameState.MAIN_MENU))


if __name__ == "__main__":
    unittest.main()
