from __future__ import annotations

from .aiplayer import AIPlayer


class OnlineAIPlayer(AIPlayer):
    def update(self, time: float = 0.0):
        super().update(time)
        self._game.get_network_session().set_local_ai_commands(self._number, self._commands)
