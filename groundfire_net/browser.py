from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
SERVER_BOOK_SCHEMA_VERSION = 1


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
        self._requested_path = Path(path) if path is not None else None
        self._path = _sqlite_path(self._requested_path) if self._requested_path is not None else None
        self._legacy_json_path = (
            self._requested_path
            if self._requested_path is not None and self._requested_path.suffix.lower() == ".json"
            else None
        )
        self._favorites: list[ServerListEntry] = []
        self._history: list[ServerListEntry] = []
        self._internet: list[ServerListEntry] = []
        self.load()

    def load(self):
        self._favorites = []
        self._history = []
        self._internet = []
        if self._path is None:
            return
        if self._path.exists():
            try:
                self._load_sqlite()
                return
            except sqlite3.Error:
                return
        legacy_payload = self._load_legacy_json()
        if not legacy_payload:
            return
        self._favorites = self._decode_entries(legacy_payload.get("favorites", ()))
        self._history = self._decode_entries(legacy_payload.get("history", ()))
        self._internet = self._decode_entries(legacy_payload.get("internet", ()))
        self.save()

    def save(self):
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._path)
        try:
            self._ensure_schema(connection)
            connection.execute("DELETE FROM server_entries")
            for bucket, entries in (
                ("favorites", self._favorites),
                ("history", self._history),
                ("internet", self._internet),
            ):
                for position, entry in enumerate(entries):
                    payload = asdict(entry)
                    connection.execute(
                        """
                        INSERT OR REPLACE INTO server_entries (
                            bucket, endpoint, position, name, host, port, game, map_name,
                            player_count, max_players, latency_ms, source, description,
                            last_played, requires_password, region, secure, protocol_version
                        )
                        VALUES (
                            :bucket, :endpoint, :position, :name, :host, :port, :game, :map_name,
                            :player_count, :max_players, :latency_ms, :source, :description,
                            :last_played, :requires_password, :region, :secure, :protocol_version
                        )
                        """,
                        {
                            **payload,
                            "bucket": bucket,
                            "endpoint": entry.endpoint,
                            "position": position,
                            "requires_password": int(entry.requires_password),
                            "secure": int(entry.secure),
                        },
                    )
            connection.commit()
        finally:
            connection.close()

    @property
    def storage_path(self) -> Path | None:
        return self._path

    def to_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "favorites": [asdict(entry) for entry in self._favorites],
            "history": [asdict(entry) for entry in self._history],
            "internet": [asdict(entry) for entry in self._internet],
        }

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
            latency_ms = raw.get("latency_ms")
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
                        latency_ms=None if latency_ms is None else int(latency_ms),
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

    def _load_sqlite(self) -> None:
        connection = sqlite3.connect(self._path)
        try:
            self._ensure_schema(connection)
            rows = connection.execute(
                """
                SELECT bucket, name, host, port, game, map_name, player_count, max_players,
                       latency_ms, source, description, last_played, requires_password,
                       region, secure, protocol_version
                FROM server_entries
                ORDER BY bucket, position, rowid
                """
            ).fetchall()
        finally:
            connection.close()
        entries_by_bucket: dict[str, list[ServerListEntry]] = {
            "favorites": [],
            "history": [],
            "internet": [],
        }
        for row in rows:
            bucket = str(row[0])
            if bucket not in entries_by_bucket:
                continue
            try:
                entries_by_bucket[bucket].append(
                    ServerListEntry(
                        name=str(row[1]),
                        host=str(row[2]),
                        port=int(row[3]),
                        game=str(row[4]),
                        map_name=str(row[5]),
                        player_count=int(row[6]),
                        max_players=int(row[7]),
                        latency_ms=None if row[8] is None else int(row[8]),
                        source=str(row[9]),
                        description=str(row[10]),
                        last_played=str(row[11]),
                        requires_password=bool(row[12]),
                        region=str(row[13]),
                        secure=bool(row[14]),
                        protocol_version=int(row[15]),
                    )
                )
            except (TypeError, ValueError):
                continue
        self._favorites = entries_by_bucket["favorites"]
        self._history = entries_by_bucket["history"]
        self._internet = entries_by_bucket["internet"]

    def _load_legacy_json(self) -> dict[str, Any]:
        if self._legacy_json_path is None or not self._legacy_json_path.exists():
            return {}
        try:
            payload = json.loads(self._legacy_json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS server_entries (
                bucket TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                position INTEGER NOT NULL,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                game TEXT NOT NULL,
                map_name TEXT NOT NULL,
                player_count INTEGER NOT NULL,
                max_players INTEGER NOT NULL,
                latency_ms INTEGER,
                source TEXT NOT NULL,
                description TEXT NOT NULL,
                last_played TEXT NOT NULL,
                requires_password INTEGER NOT NULL,
                region TEXT NOT NULL,
                secure INTEGER NOT NULL,
                protocol_version INTEGER NOT NULL,
                PRIMARY KEY (bucket, endpoint)
            )
            """
        )
        connection.execute(
            "INSERT OR REPLACE INTO metadata(key, value) VALUES('schema_version', ?)",
            (str(SERVER_BOOK_SCHEMA_VERSION),),
        )

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


def _sqlite_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.suffix.lower() in SQLITE_SUFFIXES:
        return path
    return path.with_suffix(".sqlite3")
