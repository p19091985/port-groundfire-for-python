from __future__ import annotations

from typing import Callable

from .common import GameState


MenuFactory = Callable[[object], object]


class GameFlowController:
    def __init__(self, *, menu_factories: dict[int, MenuFactory]):
        self._menu_factories = dict(menu_factories)

    def update_menu(self, game, dt: float) -> int:
        if game._current_menu is None:
            return GameState.MAIN_MENU

        return game._current_menu.update(dt)

    def enter_state(self, game, new_state: int, prev_state: int):
        if new_state == GameState.MAIN_MENU:
            if prev_state == GameState.PAUSE_MENU:
                game.delete_players()
            game._current_menu = self._create_menu(game, GameState.MAIN_MENU)
            game.get_interface().enable_mouse(True)
            game.get_interface().offset_viewport(0, 0)
            return

        if new_state == GameState.SELECT_PLAYERS_MENU:
            game._current_round = 0
            game._current_menu = self._create_menu(game, GameState.SELECT_PLAYERS_MENU)
            return

        if new_state == GameState.OPTION_MENU:
            game._current_menu = self._create_menu(game, GameState.OPTION_MENU)
            return

        if new_state == GameState.CONTROLLERS_MENU:
            game._current_menu = self._create_menu(game, GameState.CONTROLLERS_MENU)
            return

        if new_state == GameState.SET_CONTROLS_MENU:
            game._current_menu = self._create_menu(game, GameState.SET_CONTROLS_MENU)
            return

        if new_state == GameState.QUIT_MENU:
            game._current_menu = self._create_menu(game, GameState.QUIT_MENU)
            game.get_interface().enable_mouse(True)
            return

        if new_state == GameState.SHOP_MENU:
            game._current_menu = self._create_menu(game, GameState.SHOP_MENU)
            game.get_interface().enable_mouse(False)
            return

        if new_state == GameState.ROUND_SCORE:
            game._current_menu = self._create_menu(game, GameState.ROUND_SCORE)
            game.get_interface().enable_mouse(True)
            return

        if new_state == GameState.WINNER_MENU:
            game._current_menu = self._create_menu(game, GameState.WINNER_MENU)
            game.get_interface().enable_mouse(True)
            return

        if new_state == GameState.ROUND_STARTING:
            game._current_menu = None
            game.get_interface().enable_mouse(False)
            game._state_countdown = 2.0
            game._start_round()

    def is_round_state(self, state: int) -> bool:
        return state in (
            GameState.ROUND_STARTING,
            GameState.ROUND_IN_ACTION,
            GameState.ROUND_FINISHING,
        )

    def _create_menu(self, game, state: int):
        factory = self._menu_factories[state]
        return factory(game)
