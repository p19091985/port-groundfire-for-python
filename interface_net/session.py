from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

from .config import NetworkConfig

if TYPE_CHECKING:
    from src.controls import Controls
    from src.game import Game


@dataclass(frozen=True)
class NetworkPlayerRegistration:
    player_number: int
    controller: int
    name: str
    is_computer: bool


class NetworkSession:
    def __init__(self, config: NetworkConfig):
        self._config = config
        self._game: Optional["Game"] = None
        self._players: Dict[int, NetworkPlayerRegistration] = {}

    def attach_game(self, game: "Game") -> None:
        self._game = game

    def get_config(self) -> NetworkConfig:
        return self._config

    def get_registered_players(self) -> Dict[int, NetworkPlayerRegistration]:
        return dict(self._players)

    def begin_frame(self, game_time: float, dt: float) -> None:
        return None

    def end_frame(self, game_time: float, dt: float) -> None:
        return None

    def register_player(
        self,
        player_number: int,
        controller: int,
        name: str,
        is_computer: bool,
    ) -> None:
        self._players[player_number] = NetworkPlayerRegistration(
            player_number=player_number,
            controller=controller,
            name=name,
            is_computer=is_computer,
        )

    def clear_players(self) -> None:
        self._players.clear()

    def activate_online_match(self, match_setup) -> None:
        del match_setup
        return None

    def clear_online_match(self) -> None:
        return None

    def is_online_match_active(self) -> bool:
        return False

    def override_frame_dt(self, suggested_dt: float) -> float:
        return suggested_dt

    def get_landscape_seed(self, round_number: int, fallback_seed: float) -> float:
        del round_number
        return fallback_seed

    def get_tank_shuffle_seed(self, round_number: int):
        del round_number
        return None

    def set_local_ai_commands(self, player_number: int, commands) -> None:
        del player_number
        del commands
        return None

    def before_round_start(self, round_number: int) -> None:
        return None

    def after_round_end(self, round_number: int) -> None:
        return None

    def get_command(
        self,
        player_number: int,
        controller: int,
        command: int,
        controls: "Controls",
    ) -> bool:
        raise NotImplementedError
