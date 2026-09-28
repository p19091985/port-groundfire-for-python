from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version(version INTEGER PRIMARY KEY, applied_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS users(
  user_id TEXT PRIMARY KEY, handle TEXT UNIQUE, display_name TEXT NOT NULL,
  user_type TEXT NOT NULL CHECK(user_type IN ('guest','account','operator')),
  password_hash TEXT, status TEXT NOT NULL DEFAULT 'active', revision INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions(
  session_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  access_hash TEXT UNIQUE NOT NULL, refresh_hash TEXT UNIQUE NOT NULL,
  access_expires_at REAL NOT NULL, refresh_expires_at REAL NOT NULL,
  device_name TEXT NOT NULL, revoked_at REAL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS presence(
  user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  availability TEXT NOT NULL, expires_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS friend_requests(
  request_id TEXT PRIMARY KEY, sender_id TEXT NOT NULL REFERENCES users(user_id),
  recipient_id TEXT NOT NULL REFERENCES users(user_id), state TEXT NOT NULL, created_at REAL NOT NULL,
  UNIQUE(sender_id, recipient_id)
);
CREATE TABLE IF NOT EXISTS friendships(
  user_low TEXT NOT NULL REFERENCES users(user_id), user_high TEXT NOT NULL REFERENCES users(user_id),
  created_at REAL NOT NULL, PRIMARY KEY(user_low,user_high)
);
CREATE TABLE IF NOT EXISTS blocks(
  blocker_id TEXT NOT NULL REFERENCES users(user_id), blocked_id TEXT NOT NULL REFERENCES users(user_id),
  created_at REAL NOT NULL, PRIMARY KEY(blocker_id,blocked_id)
);
CREATE TABLE IF NOT EXISTS parties(
  party_id TEXT PRIMARY KEY, leader_id TEXT NOT NULL REFERENCES users(user_id),
  revision INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS party_members(
  party_id TEXT NOT NULL REFERENCES parties(party_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id), joined_at REAL NOT NULL,
  ready_revision INTEGER, PRIMARY KEY(party_id,user_id), UNIQUE(user_id)
);
CREATE TABLE IF NOT EXISTS lobbies(
  lobby_id TEXT PRIMARY KEY, name TEXT NOT NULL, leader_id TEXT NOT NULL REFERENCES users(user_id),
  visibility TEXT NOT NULL, password_hash TEXT, state TEXT NOT NULL DEFAULT 'open',
  capacity INTEGER NOT NULL, rounds INTEGER NOT NULL, map_id TEXT NOT NULL, seed INTEGER NOT NULL,
  bots INTEGER NOT NULL DEFAULT 0, revision INTEGER NOT NULL DEFAULT 1,
  match_id TEXT, expires_at REAL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS lobby_members(
  lobby_id TEXT NOT NULL REFERENCES lobbies(lobby_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id), role TEXT NOT NULL DEFAULT 'player',
  ready_revision INTEGER, joined_at REAL NOT NULL,
  PRIMARY KEY(lobby_id,user_id), UNIQUE(user_id)
);
CREATE TABLE IF NOT EXISTS invites(
  invite_id TEXT PRIMARY KEY, code_hash TEXT UNIQUE, sender_id TEXT NOT NULL REFERENCES users(user_id),
  recipient_id TEXT REFERENCES users(user_id), target_type TEXT NOT NULL, target_id TEXT NOT NULL,
  max_uses INTEGER NOT NULL DEFAULT 1, use_count INTEGER NOT NULL DEFAULT 0,
  expires_at REAL NOT NULL, revoked_at REAL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS queue_tickets(
  queue_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(user_id), party_id TEXT,
  party_revision INTEGER, criteria_json TEXT NOT NULL, state TEXT NOT NULL,
  reservation_id TEXT, expires_at REAL NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations(
  reservation_id TEXT PRIMARY KEY, lobby_id TEXT NOT NULL REFERENCES lobbies(lobby_id),
  state TEXT NOT NULL, expires_at REAL NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS matches(
  match_id TEXT PRIMARY KEY, lobby_id TEXT NOT NULL REFERENCES lobbies(lobby_id),
  reservation_id TEXT NOT NULL REFERENCES reservations(reservation_id), generation INTEGER NOT NULL DEFAULT 1,
  state TEXT NOT NULL, runtime_version TEXT NOT NULL, session_secret TEXT NOT NULL,
  udp_host TEXT, udp_port INTEGER, websocket_url TEXT, worker_pid INTEGER, gateway_pid INTEGER,
  failure_code TEXT, started_at REAL, stopped_at REAL, created_at REAL NOT NULL,
  UNIQUE(lobby_id, generation)
);
CREATE TABLE IF NOT EXISTS reservation_members(
  reservation_id TEXT NOT NULL REFERENCES reservations(reservation_id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(user_id), accepted INTEGER NOT NULL DEFAULT 0,
  admission_hash TEXT, admission_used_at REAL,
  PRIMARY KEY(reservation_id,user_id)
);
CREATE TABLE IF NOT EXISTS events(
  sequence INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL REFERENCES users(user_id),
  event_id TEXT UNIQUE NOT NULL, event_type TEXT NOT NULL, resource_id TEXT,
  revision INTEGER, data_json TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS event_tickets(
  ticket_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  expires_at REAL NOT NULL, used_at REAL
);
CREATE TABLE IF NOT EXISTS chat_messages(
  sequence INTEGER PRIMARY KEY AUTOINCREMENT, message_id TEXT UNIQUE NOT NULL,
  channel_type TEXT NOT NULL, channel_id TEXT NOT NULL,
  author_id TEXT NOT NULL REFERENCES users(user_id), client_message_id TEXT NOT NULL,
  text TEXT NOT NULL, created_at REAL NOT NULL,
  UNIQUE(author_id,client_message_id)
);
CREATE TABLE IF NOT EXISTS idempotency(
  principal_id TEXT NOT NULL, route TEXT NOT NULL, request_key TEXT NOT NULL,
  request_hash TEXT NOT NULL, response_json TEXT NOT NULL, expires_at REAL NOT NULL,
  PRIMARY KEY(principal_id,route,request_key)
);
CREATE INDEX IF NOT EXISTS idx_events_user_sequence ON events(user_id,sequence);
CREATE INDEX IF NOT EXISTS idx_sessions_access ON sessions(access_hash);
CREATE INDEX IF NOT EXISTS idx_invites_expiry ON invites(expires_at);
CREATE INDEX IF NOT EXISTS idx_queues_expiry ON queue_tickets(expires_at);
CREATE INDEX IF NOT EXISTS idx_reservations_expiry ON reservations(expires_at);
CREATE INDEX IF NOT EXISTS idx_matches_lobby ON matches(lobby_id,state);
CREATE INDEX IF NOT EXISTS idx_chat_channel ON chat_messages(channel_type,channel_id,sequence);
"""


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._migration_lock = threading.Lock()
        self.migrate()

    def connection(self) -> sqlite3.Connection:
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(self.path, timeout=15.0, isolation_level=None, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA busy_timeout=15000")
            self._local.connection = connection
        return connection

    def migrate(self) -> None:
        with self._migration_lock:
            connection = self.connection()
            connection.executescript(SCHEMA)
            connection.execute("INSERT OR IGNORE INTO schema_version(version,applied_at) VALUES(1,?)", (time.time(),))

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        connection = self.connection()
        connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        else:
            connection.commit()

    def one(self, query: str, parameters: tuple = ()) -> sqlite3.Row | None:
        return self.connection().execute(query, parameters).fetchone()

    def all(self, query: str, parameters: tuple = ()) -> list[sqlite3.Row]:
        return list(self.connection().execute(query, parameters).fetchall())

    def cleanup(self, now: float | None = None) -> None:
        moment = now or time.time()
        with self.transaction(immediate=True) as db:
            db.execute(
                "DELETE FROM sessions WHERE refresh_expires_at <= ? OR (revoked_at IS NOT NULL AND revoked_at < ?)",
                (moment, moment - 86400),
            )
            db.execute("DELETE FROM idempotency WHERE expires_at <= ?", (moment,))
            db.execute(
                "UPDATE queue_tickets SET state='expired' WHERE state='searching' AND expires_at <= ?", (moment,)
            )
            db.execute(
                "UPDATE reservations SET state='expired' WHERE state IN ('held','accepted','preparing') AND expires_at <= ?",
                (moment,),
            )
            db.execute("DELETE FROM events WHERE created_at < ?", (moment - 7 * 86400,))
            db.execute("DELETE FROM event_tickets WHERE expires_at <= ? OR used_at IS NOT NULL", (moment,))

    def emit(
        self,
        db: sqlite3.Connection,
        user_ids: list[str],
        event_type: str,
        resource_id: str | None,
        revision: int | None,
        data: dict,
    ) -> None:
        from .security import new_id

        encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        now = time.time()
        for user_id in sorted(set(user_ids)):
            db.execute(
                "INSERT INTO events(user_id,event_id,event_type,resource_id,revision,data_json,created_at) VALUES(?,?,?,?,?,?,?)",
                (user_id, new_id("evt"), event_type, resource_id, revision, encoded, now),
            )
