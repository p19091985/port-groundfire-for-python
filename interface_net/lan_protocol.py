from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple


LAN_DISCOVERY_PORT = 37021


@dataclass(frozen=True)
class LanPlayerDescriptor:
    slot_index: int
    name: str
    uses_ai: bool = False

    def to_payload(self) -> Dict[str, Any]:
        return {
            "slot_index": self.slot_index,
            "name": self.name,
            "uses_ai": self.uses_ai,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "LanPlayerDescriptor":
        return cls(
            slot_index=int(payload.get("slot_index", 0)),
            name=str(payload.get("name", "Player")),
            uses_ai=bool(payload.get("uses_ai", False)),
        )


@dataclass(frozen=True)
class LanLobbySnapshot:
    server_name: str
    map_name: str
    network: str
    host: str
    port: int
    max_players: int
    current_players: int
    secure: bool
    players: Tuple[str, ...]
    player_slots: Tuple[LanPlayerDescriptor, ...]
    rounds: int
    lobby_state: str
    countdown_seconds: int
    match_started: bool
    match_id: str
    landscape_seed: int
    tank_seed: int

    def to_payload(self) -> Dict[str, Any]:
        return {
            "server_name": self.server_name,
            "map_name": self.map_name,
            "network": self.network,
            "host": self.host,
            "port": self.port,
            "max_players": self.max_players,
            "current_players": self.current_players,
            "secure": self.secure,
            "players": list(self.players),
            "player_slots": [player.to_payload() for player in self.player_slots],
            "rounds": self.rounds,
            "lobby_state": self.lobby_state,
            "countdown_seconds": self.countdown_seconds,
            "match_started": self.match_started,
            "match_id": self.match_id,
            "landscape_seed": self.landscape_seed,
            "tank_seed": self.tank_seed,
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "LanLobbySnapshot":
        player_slots = tuple(
            LanPlayerDescriptor.from_payload(player_payload)
            for player_payload in payload.get("player_slots", [])
        )
        players = payload.get("players")
        if players is None:
            players = [player.name for player in player_slots]
        return cls(
            server_name=str(payload["server_name"]),
            map_name=str(payload["map_name"]),
            network=str(payload["network"]),
            host=str(payload["host"]),
            port=int(payload["port"]),
            max_players=int(payload["max_players"]),
            current_players=int(payload["current_players"]),
            secure=bool(payload["secure"]),
            players=tuple(str(player_name) for player_name in players),
            player_slots=player_slots,
            rounds=int(payload.get("rounds", 10)),
            lobby_state=str(payload.get("lobby_state", "waiting")),
            countdown_seconds=int(payload.get("countdown_seconds", 0)),
            match_started=bool(payload.get("match_started", False)),
            match_id=str(payload.get("match_id", "")),
            landscape_seed=int(payload.get("landscape_seed", 0)),
            tank_seed=int(payload.get("tank_seed", 0)),
        )
