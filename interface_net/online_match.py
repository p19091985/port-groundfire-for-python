from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .lan_client import LanConnectionResult


@dataclass(frozen=True)
class OnlineMatchPlayer:
    player_number: int
    name: str
    is_local: bool
    uses_ai: bool


@dataclass(frozen=True)
class OnlineMatchSetup:
    match_id: str
    host: str
    port: int
    player_id: str
    local_player_slot: int
    rounds: int
    landscape_seed: int
    tank_seed: int
    players: Tuple[OnlineMatchPlayer, ...]

    @classmethod
    def from_connection_result(cls, result: LanConnectionResult) -> "OnlineMatchSetup":
        players = tuple(
            OnlineMatchPlayer(
                player_number=player.slot_index,
                name=player.name,
                is_local=player.slot_index == result.slot_index,
                uses_ai=player.uses_ai,
            )
            for player in result.player_slots
        )
        return cls(
            match_id=result.match_id,
            host=result.host,
            port=result.port,
            player_id=result.player_id,
            local_player_slot=result.slot_index,
            rounds=result.rounds,
            landscape_seed=result.landscape_seed,
            tank_seed=result.tank_seed,
            players=players,
        )
