from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from .world import ReplicatedEntityState


@dataclass(frozen=True)
class ReplicatedPlayerState:
    player_number: int
    name: str
    score: int = 0
    money: int = 0
    connected: bool = True
    is_computer: bool = False
    tank_entity_id: int | None = None
    acknowledged_command_sequence: int = 0
    acknowledged_snapshot_sequence: int = 0
    colour: tuple[int, int, int] = (255, 255, 255)
    is_leader: bool = False
    selected_weapon: str = "shell"
    weapon_stocks: tuple[tuple[str, int], ...] = ()
    round_defeated_player_numbers: tuple[int, ...] = ()


@dataclass(frozen=True)
class MatchSnapshot:
    authority: str
    game_phase: str
    current_round: int
    num_rounds: int
    simulation_tick: int
    players: tuple[ReplicatedPlayerState, ...]
    entities: tuple[ReplicatedEntityState, ...]
    phase_ticks_remaining: int = 0
    round_winner_player_number: int | None = None
    winner_player_number: int | None = None
    seed: int = 0
    world_width: float = 11.0
    terrain_revision: int = 0
    terrain_profile: tuple[float, ...] = ()


@dataclass
class MatchState:
    session_id: str
    authority: str = "server"
    game_phase: str = "lobby"
    current_round: int = 0
    num_rounds: int = 10
    simulation_tick: int = 0
    phase_ticks_remaining: int = 0
    round_winner_player_number: int | None = None
    winner_player_number: int | None = None
    player_slots: dict[int, ReplicatedPlayerState] = field(default_factory=dict)
    _events: list[dict[str, Any]] = field(default_factory=list)

    def upsert_player(self, player: ReplicatedPlayerState):
        self.player_slots[player.player_number] = player

    def update_player(self, player_number: int, **changes):
        player = self.player_slots[player_number]
        self.player_slots[player_number] = replace(player, **changes)

    def remove_player(self, player_number: int):
        self.player_slots.pop(player_number, None)

    def get_player(self, player_number: int) -> ReplicatedPlayerState | None:
        return self.player_slots.get(player_number)

    def queue_event(self, event_type: str, **payload):
        self._events.append({"event_type": event_type, "payload": dict(payload)})

    def drain_events(self) -> tuple[dict[str, Any], ...]:
        drained = tuple(self._events)
        self._events.clear()
        return drained

    def snapshot(
        self,
        entities: tuple[ReplicatedEntityState, ...],
        *,
        seed: int = 0,
        world_width: float = 11.0,
        terrain_revision: int = 0,
        terrain_profile: tuple[float, ...] = (),
    ) -> MatchSnapshot:
        players = tuple(self.player_slots[player_number] for player_number in sorted(self.player_slots))
        return MatchSnapshot(
            authority=self.authority,
            game_phase=self.game_phase,
            current_round=self.current_round,
            num_rounds=self.num_rounds,
            simulation_tick=self.simulation_tick,
            players=players,
            entities=entities,
            phase_ticks_remaining=self.phase_ticks_remaining,
            round_winner_player_number=self.round_winner_player_number,
            winner_player_number=self.winner_player_number,
            seed=seed,
            world_width=world_width,
            terrain_revision=terrain_revision,
            terrain_profile=terrain_profile,
        )
