from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ServerListEntry:
    name: str
    host: str
    port: int
    game: str = "Groundfire"
    map_name: str = "generated"
    player_count: int = 0
    max_players: int = 8
    latency_ms: int | None = None
    source: str = "lan"
    description: str = ""
    last_played: str = ""
    requires_password: bool = False
    region: str = "world"
    secure: bool = True
    protocol_version: int = 1

    @property
    def endpoint(self) -> str:
        return f"{self.host}:{self.port}"

    def with_updates(self, **updates) -> "ServerListEntry":
        payload = asdict(self)
        payload.update(updates)
        return ServerListEntry(**payload)


class ServerBook:
    def __init__(self, path: str | Path | None = None):
        self._path = Path(path) if path is not None else None
        self._favorites: list[ServerListEntry] = []
        self._history: list[ServerListEntry] = []
        self._internet: list[ServerListEntry] = []
        self.load()

    def load(self):
        if self._path is None or not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self._favorites = self._decode_entries(payload.get("favorites", ()))
        self._history = self._decode_entries(payload.get("history", ()))
        self._internet = self._decode_entries(payload.get("internet", ()))

    def save(self):
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "favorites": [asdict(entry) for entry in self._favorites],
            "history": [asdict(entry) for entry in self._history],
            "internet": [asdict(entry) for entry in self._internet],
        }
        self._path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def get_favorites(self) -> tuple[ServerListEntry, ...]:
        return tuple(self._favorites)

    def get_history(self) -> tuple[ServerListEntry, ...]:
        return tuple(self._history)

    def get_internet(self) -> tuple[ServerListEntry, ...]:
        return tuple(self._internet)

    def add_favorite(self, entry: ServerListEntry):
        self._favorites = self._upsert(self._favorites, entry.with_updates(source="favorite"))
        self.save()

    def add_manual_server(self, host: str, port: int, *, name: str | None = None) -> ServerListEntry:
        entry = ServerListEntry(
            name=name or f"{host}:{port}",
            host=host,
            port=port,
            source="favorite",
            latency_ms=None,
        )
        self.add_favorite(entry)
        return entry

    def record_history(self, entry: ServerListEntry):
        self._history = self._upsert(
            self._history,
            entry.with_updates(source="history", last_played=datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        self.save()

    def set_internet_servers(self, entries: tuple[ServerListEntry, ...]):
        self._internet = [entry.with_updates(source="internet") for entry in entries]
        self.save()

    def update_entry(self, entry: ServerListEntry):
        if entry.source == "favorite":
            self._favorites = self._upsert(self._favorites, entry)
        elif entry.source == "history":
            self._history = self._upsert(self._history, entry)
        elif entry.source == "internet":
            self._internet = self._upsert(self._internet, entry)
        self.save()

    def entries_for_tab(
        self,
        tab: str,
        *,
        lan_entries: tuple[ServerListEntry, ...] = (),
    ) -> tuple[ServerListEntry, ...]:
        if tab == "lan":
            return lan_entries
        if tab == "favorites":
            return tuple(self._favorites)
        if tab == "history":
            return tuple(self._history)
        if tab == "unique":
            return self._unique(tuple(self._internet) + lan_entries + tuple(self._favorites) + tuple(self._history))
        if tab == "internet":
            return tuple(self._internet)
        return self._unique(tuple(self._internet) + lan_entries + tuple(self._favorites))

    def all_entries(
        self,
        *,
        lan_entries: tuple[ServerListEntry, ...] = (),
    ) -> tuple[ServerListEntry, ...]:
        return self._unique(tuple(self._internet) + lan_entries + tuple(self._favorites) + tuple(self._history))

    def _decode_entries(self, raw_entries) -> list[ServerListEntry]:
        entries = []
        for raw in raw_entries:
            if not isinstance(raw, dict):
                continue
            try:
                entries.append(
                    ServerListEntry(
                        name=str(raw.get("name", "Server")),
                        host=str(raw.get("host", "127.0.0.1")),
                        port=int(raw.get("port", 27015)),
                        game=str(raw.get("game", "Groundfire")),
                        map_name=str(raw.get("map_name", "generated")),
                        player_count=int(raw.get("player_count", 0)),
                        max_players=int(raw.get("max_players", 8)),
                        latency_ms=None if raw.get("latency_ms") is None else int(raw.get("latency_ms")),
                        source=str(raw.get("source", "favorite")),
                        description=str(raw.get("description", "")),
                        last_played=str(raw.get("last_played", "")),
                        requires_password=bool(raw.get("requires_password", False)),
                        region=str(raw.get("region", "world")),
                        secure=bool(raw.get("secure", True)),
                        protocol_version=int(raw.get("protocol_version", 1)),
                    )
                )
            except (TypeError, ValueError):
                continue
        return entries

    def _upsert(
        self,
        entries: list[ServerListEntry],
        entry: ServerListEntry,
    ) -> list[ServerListEntry]:
        filtered = [candidate for candidate in entries if candidate.endpoint != entry.endpoint]
        return [entry] + filtered[:49]

    def _unique(self, entries: tuple[ServerListEntry, ...]) -> tuple[ServerListEntry, ...]:
        seen: set[str] = set()
        unique = []
        for entry in entries:
            if entry.endpoint in seen:
                continue
            seen.add(entry.endpoint)
            unique.append(entry)
        return tuple(unique)
