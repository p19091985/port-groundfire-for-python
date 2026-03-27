from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json

from .networkstate import MatchSnapshot


@dataclass(frozen=True)
class ClientCommandEnvelope:
    session_id: str
    player_number: int
    client_sequence: int
    acknowledged_snapshot_sequence: int | None
    simulation_tick: int
    issued_at: float
    source: str
    commands: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerSnapshotEnvelope:
    session_id: str
    snapshot_sequence: int
    simulation_tick: int
    acknowledged_command_sequences: dict[int, int]
    snapshot: MatchSnapshot


class ClientServerEnvelopeBuilder:
    def __init__(self):
        self._next_command_sequence_by_player: dict[int, int] = {}
        self._last_command_sequence_by_player: dict[int, int] = {}
        self._last_snapshot_sequence = 0

    def build_command_envelopes(self, game) -> tuple[ClientCommandEnvelope, ...]:
        envelopes = []
        for player_number in range(game.get_num_of_players()):
            player = game.get_players()[player_number]
            if player is None:
                continue

            for frame in player.drain_intent_frames():
                sequence = self._next_command_sequence_by_player.get(player_number, 1)
                self._next_command_sequence_by_player[player_number] = sequence + 1
                self._last_command_sequence_by_player[player_number] = sequence
                envelopes.append(
                    ClientCommandEnvelope(
                        session_id=game.get_session_id(),
                        player_number=player_number,
                        client_sequence=sequence,
                        acknowledged_snapshot_sequence=self._last_snapshot_sequence or None,
                        simulation_tick=game.get_simulation_tick(),
                        issued_at=frame.simulation_time,
                        source=frame.source,
                        commands=frame.to_dict(),
                    )
                )
        return tuple(envelopes)

    def build_snapshot_envelope(self, game, snapshot: MatchSnapshot) -> ServerSnapshotEnvelope:
        self._last_snapshot_sequence += 1
        return ServerSnapshotEnvelope(
            session_id=game.get_session_id(),
            snapshot_sequence=self._last_snapshot_sequence,
            simulation_tick=game.get_simulation_tick(),
            acknowledged_command_sequences=dict(self._last_command_sequence_by_player),
            snapshot=snapshot,
        )

    def serialize_command_envelope(self, envelope: ClientCommandEnvelope) -> str:
        return json.dumps(asdict(envelope), sort_keys=True)

    def serialize_snapshot_envelope(self, envelope: ServerSnapshotEnvelope) -> str:
        return json.dumps(asdict(envelope), sort_keys=True)
