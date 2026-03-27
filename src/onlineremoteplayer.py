from __future__ import annotations

from .humanplayer import HumanPlayer


class OnlineRemotePlayer(HumanPlayer):
    def __init__(self, game, number: int, name: str, colour: tuple, controller: int, controls, uses_ai: bool = False):
        super().__init__(game, number, name, colour, controller, controls)
        self._uses_ai = uses_ai

    def is_computer(self) -> bool:
        return self._uses_ai
