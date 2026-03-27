from typing import TYPE_CHECKING, List, Optional

from .commandintents import ALL_PLAYER_COMMANDS, PlayerIntentFrame
from .player import Player

if TYPE_CHECKING:
    from .controls import Controls
    from .game import Game


class HumanPlayer(Player):
    def __init__(self, game: "Game", number: int, name: str, colour: tuple, controller: int, controls: "Controls"):
        super().__init__(game, number, name, colour)
        self._controller = controller
        self._controls = controls

    def get_controller(self) -> int:
        return self._controller

    def update(self, time: float = 0.0):
        self._refresh_intents()

    def get_command(self, command: int, start_time_ref: Optional[List[float]] = None) -> bool:
        if not hasattr(self, "_current_intents"):
            if start_time_ref and len(start_time_ref) > 0:
                start_time_ref[0] = 0.0
            return self._controls.get_command(self._controller, command)

        self._refresh_intents()
        return super().get_command(command, start_time_ref)

    def _refresh_intents(self):
        command_states = [
            self._controls.get_command(self._controller, int(command))
            for command in ALL_PLAYER_COMMANDS
        ]
        self.publish_intents(
            PlayerIntentFrame.from_iterable(
                command_states,
                source=f"human:{self._controller}",
                simulation_time=self._get_simulation_time(),
            )
        )
