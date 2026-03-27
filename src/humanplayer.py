from .player import Player
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .game import Game
    from .controls import Controls

class HumanPlayer(Player):
    def __init__(self, game: 'Game', number: int, name: str, colour: tuple, controller: int, controls: 'Controls'):
        super().__init__(game, number, name, colour)
        self._controller = controller
        self._controls = controls

    def get_controller(self) -> int:
        return self._controller

    def get_command(self, command: int, start_time_ref: Optional[List[float]] = None) -> bool:
        if isinstance(start_time_ref, list) and start_time_ref:
            start_time_ref[0] = 0.0

        return self._game.get_network_session().get_command(
            self._number,
            self._controller,
            command,
            self._controls,
        )
