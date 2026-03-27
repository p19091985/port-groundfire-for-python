from typing import TYPE_CHECKING

import pygame

from interface_net import NetworkClientInterface

from .common import GameState
from .menu import Menu

if TYPE_CHECKING:
    from .game import Game


class FindServersMenu(Menu):
    def __init__(self, game: "Game"):
        super().__init__(game)
        width, height, _fullscreen = game.get_interface().get_window_settings()
        self._client_interface = NetworkClientInterface(width, height, game.get_settings())
        self._key_down = getattr(pygame, "KEYDOWN", 768)
        self._escape_key = getattr(pygame, "K_ESCAPE", 27)

    def update(self, time: float) -> int:
        self._client_interface.update(time)
        match_setup = self._client_interface.consume_match_setup()
        if match_setup is not None:
            self._game.prepare_online_match(match_setup)
            return GameState.ROUND_STARTING

        for event in pygame.event.get():
            if getattr(event, "type", None) == self._key_down and getattr(event, "key", None) == self._escape_key:
                self._client_interface.shutdown()
                return GameState.MAIN_MENU

            action = self._client_interface.handle_event(event)
            if action is not None and action.kind == "close":
                self._client_interface.shutdown()
                return GameState.MAIN_MENU

        return GameState.CURRENT_STATE

    def draw(self):
        self._client_interface.draw_to_interface(self._game.get_interface())
