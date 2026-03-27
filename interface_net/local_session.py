from __future__ import annotations

from .session import NetworkSession


class LocalNetworkSession(NetworkSession):
    def get_command(self, player_number: int, controller: int, command: int, controls) -> bool:
        del player_number
        return controls.get_command(controller, command)
