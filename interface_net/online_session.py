from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

from .config import NetworkConfig
from .lan_client import LanClient
from .online_match import OnlineMatchSetup
from .session import NetworkSession


class HybridNetworkSession(NetworkSession):
    ONLINE_COMMAND_COUNT = 11
    ONLINE_FIXED_DT = 1.0 / 30.0

    def __init__(self, config: NetworkConfig):
        super().__init__(config)
        self._lan_client = LanClient()
        self._active_match: Optional[OnlineMatchSetup] = None
        self._frame_index = 0
        self._local_commands = [False] * self.ONLINE_COMMAND_COUNT
        self._remote_commands: Dict[int, Tuple[bool, ...]] = {}

    def activate_online_match(self, match_setup: OnlineMatchSetup) -> None:
        self._active_match = match_setup
        self._frame_index = 0
        self._local_commands = [False] * self.ONLINE_COMMAND_COUNT
        self._remote_commands = {
            player.player_number: tuple(False for _ in range(self.ONLINE_COMMAND_COUNT))
            for player in match_setup.players
            if player.player_number != match_setup.local_player_slot
        }

    def clear_online_match(self) -> None:
        if self._active_match is not None:
            try:
                self._lan_client.leave(
                    host=self._active_match.host,
                    port=self._active_match.port,
                    player_id=self._active_match.player_id,
                    timeout=0.15,
                )
            except OSError:
                pass
        self._active_match = None
        self._frame_index = 0
        self._local_commands = [False] * self.ONLINE_COMMAND_COUNT
        self._remote_commands = {}

    def is_online_match_active(self) -> bool:
        return self._active_match is not None

    def override_frame_dt(self, suggested_dt: float) -> float:
        if self._active_match is None:
            return suggested_dt
        return self.ONLINE_FIXED_DT

    def get_landscape_seed(self, round_number: int, fallback_seed: float) -> float:
        if self._active_match is None:
            return fallback_seed
        return (self._active_match.landscape_seed + (round_number * 9973)) / 1000.0

    def get_tank_shuffle_seed(self, round_number: int):
        if self._active_match is None:
            return None
        return self._active_match.tank_seed + (round_number * 7919)

    def set_local_ai_commands(self, player_number: int, commands: Sequence[bool]) -> None:
        if self._active_match is None:
            return
        if player_number != self._active_match.local_player_slot:
            return
        normalized = [False] * self.ONLINE_COMMAND_COUNT
        for index, command in enumerate(tuple(bool(value) for value in commands)[: self.ONLINE_COMMAND_COUNT]):
            normalized[index] = command
        self._local_commands = normalized

    def end_frame(self, game_time: float, dt: float) -> None:
        del game_time
        del dt
        if self._active_match is None or self._game is None:
            return

        try:
            sync_result = self._lan_client.sync_frame(
                host=self._active_match.host,
                port=self._active_match.port,
                player_id=self._active_match.player_id,
                frame_index=self._frame_index,
                commands=self._local_commands,
                current_round=self._game.get_current_round(),
            )
        except OSError:
            return

        if sync_result.status != "ok":
            return

        self._remote_commands = {
            slot_index: tuple(commands[: self.ONLINE_COMMAND_COUNT])
            for slot_index, commands in sync_result.commands_by_slot.items()
            if slot_index != self._active_match.local_player_slot
        }
        self._frame_index += 1
        self._local_commands = [False] * self.ONLINE_COMMAND_COUNT

    def get_command(
        self,
        player_number: int,
        controller: int,
        command: int,
        controls,
    ) -> bool:
        if self._active_match is None:
            return controls.get_command(controller, command)

        if player_number == self._active_match.local_player_slot:
            state = controls.get_command(controller, command)
            if 0 <= command < self.ONLINE_COMMAND_COUNT:
                self._local_commands[command] = state
            return state

        remote_commands = self._remote_commands.get(player_number)
        if remote_commands is None or not (0 <= command < len(remote_commands)):
            return False
        return bool(remote_commands[command])
