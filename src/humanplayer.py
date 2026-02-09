from .player import Player
from typing import TYPE_CHECKING, List

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

    def get_command(self, command: int, start_time_ref: List[float]) -> bool:
        if start_time_ref and len(start_time_ref) > 0:
            start_time_ref[0] = 0.0
            
        return self._controls.get_command(self._controller, command)
