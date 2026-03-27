from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json


@dataclass(frozen=True)
class NetworkEvent:
    event_type: str
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class EntitySnapshot:
    entity_id: int
    entity_type: str
    position: tuple[float, float]
    payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class PlayerSnapshot:
    player_number: int
    name: str
    score: int
    money: int
    is_computer: bool
    tank_entity_id: int | None
    intents: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchSnapshot:
    authority: str
    game_state: int
    current_round: int
    num_rounds: int
    entities: tuple[EntitySnapshot, ...]
    players: tuple[PlayerSnapshot, ...]
    events: tuple[NetworkEvent, ...] = field(default_factory=tuple)


class MatchNetworkStateBuilder:
    AUTHORITY_SERVER = "server"

    def __init__(self, *, entity_adapter=None):
        self._entity_adapter = entity_adapter

    def build_snapshot(self, game) -> MatchSnapshot:
        entity_snapshots = []
        for entity in game._entity_list:
            if self._entity_adapter is not None:
                snapshot = self._entity_adapter.build_snapshot(game, entity)
            elif hasattr(entity, "build_network_snapshot"):
                snapshot = entity.build_network_snapshot()
            else:
                snapshot = EntitySnapshot(
                    entity_id=entity.get_entity_id() if hasattr(entity, "get_entity_id") else -1,
                    entity_type=entity.get_entity_type() if hasattr(entity, "get_entity_type") else type(entity).__name__.lower(),
                    position=entity.get_position() if hasattr(entity, "get_position") else (0.0, 0.0),
                    payload={},
                )
            entity_snapshots.append(snapshot)

        player_snapshots = []
        for index in range(game.get_num_of_players()):
            player = game.get_players()[index]
            if player is None:
                continue
            player_snapshots.append(
                PlayerSnapshot(
                    player_number=index,
                    name=player.get_name(),
                    score=player.get_score(),
                    money=player.get_money(),
                    is_computer=player.is_computer(),
                    tank_entity_id=player.get_tank().get_entity_id() if player.get_tank() else None,
                    intents=player.get_current_intents().to_dict(),
                )
            )

        return MatchSnapshot(
            authority=self.AUTHORITY_SERVER,
            game_state=game.get_game_state(),
            current_round=game.get_current_round(),
            num_rounds=game.get_num_of_rounds(),
            entities=tuple(entity_snapshots),
            players=tuple(player_snapshots),
            events=tuple(game.get_pending_network_events()),
        )

    def serialize_snapshot(self, snapshot: MatchSnapshot) -> str:
        return json.dumps(asdict(snapshot), sort_keys=True)
