from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable
from typing import Any

from groundfire_net.websocket_gateway import generate_join_token

from .config import Settings
from .errors import ServiceError, bad_request, conflict, forbidden, not_found
from .security import (
    hash_password,
    new_id,
    new_secret,
    normalize_handle,
    token_hash,
    validate_display_name,
    verify_password,
)
from .store import Store


class GroundfireService:
    def __init__(self, store: Store, settings: Settings, *, clock: Callable[[], float] = time.time):
        self.store = store
        self.settings = settings
        self.clock = clock

    def capabilities(self) -> dict[str, Any]:
        return {
            "service_version": "0.1.0",
            "api_versions": [1],
            "social_ws_versions": [1],
            "managed_game_protocols": {"websocket": [2], "udp": []},
            "legacy_game_protocols": {"websocket": [1, 2], "udp": [1]},
            "enabled_transports": ["ws"],
            "features": {
                "accounts": True,
                "guests": True,
                "friends": True,
                "parties": True,
                "hosted_lobbies": True,
                "matchmaking": True,
                "spectators": True,
                "join_in_progress": False,
            },
            "limits": {
                "party_members": 8,
                "match_players_min": 2,
                "match_players_max": 8,
                "match_spectators": 8,
                "rounds_min": 5,
                "rounds_max": 50,
            },
            "timers_seconds": {
                "presence_heartbeat": 20,
                "presence_ttl": self.settings.presence_ttl_seconds,
                "reservation_ttl": self.settings.reservation_ttl_seconds,
                "queue_ttl": self.settings.queue_ttl_seconds,
                "reconnect_window": 60,
            },
            "capacity": {"accepting_allocations": True, "worker_limit": self.settings.max_workers},
            "maps": [
                {"id": "classic", "default_seed": 1},
                {"id": "basin", "default_seed": 7},
                {"id": "ridge", "default_seed": 11},
                {"id": "crater", "default_seed": 17},
                {"id": "mesa", "default_seed": 23},
            ],
        }

    def register(self, handle: str, display_name: str, password: str, device_name: str = "Groundfire") -> dict:
        try:
            normalized = normalize_handle(handle)
            shown = validate_display_name(display_name)
            encoded = hash_password(password)
        except ValueError as exc:
            raise bad_request("invalid_identity", str(exc)) from exc
        user_id = new_id("usr")
        now = self.clock()
        try:
            with self.store.transaction(immediate=True) as db:
                db.execute(
                    "INSERT INTO users(user_id,handle,display_name,user_type,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                    (user_id, normalized, shown, "account", encoded, now),
                )
        except sqlite3.IntegrityError as exc:
            raise conflict("handle_unavailable", "Esse identificador já está em uso.") from exc
        return self._create_session(user_id, device_name)

    def guest(self, display_name: str, device_name: str = "Groundfire") -> dict:
        try:
            shown = validate_display_name(display_name)
        except ValueError as exc:
            raise bad_request("invalid_identity", str(exc)) from exc
        user_id = new_id("usr")
        with self.store.transaction(immediate=True) as db:
            db.execute(
                "INSERT INTO users(user_id,handle,display_name,user_type,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                (user_id, None, shown, "guest", None, self.clock()),
            )
        return self._create_session(user_id, device_name)

    def login(self, handle: str, password: str, device_name: str = "Groundfire") -> dict:
        try:
            normalized = normalize_handle(handle)
        except ValueError:
            normalized = ""
        row = self.store.one("SELECT * FROM users WHERE handle=? AND status='active'", (normalized,))
        if row is None or not row["password_hash"] or not verify_password(row["password_hash"], password):
            raise ServiceError(401, "invalid_credentials", "Credenciais inválidas.")
        return self._create_session(row["user_id"], device_name)

    def _create_session(self, user_id: str, device_name: str) -> dict:
        session_id = new_id("ses")
        access = new_secret()
        refresh = new_secret()
        now = self.clock()
        access_expiry = now + self.settings.access_ttl_seconds
        refresh_expiry = now + self.settings.refresh_ttl_seconds
        with self.store.transaction(immediate=True) as db:
            db.execute(
                "INSERT INTO sessions(session_id,user_id,access_hash,refresh_hash,access_expires_at,refresh_expires_at,device_name,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (
                    session_id,
                    user_id,
                    token_hash(access),
                    token_hash(refresh),
                    access_expiry,
                    refresh_expiry,
                    str(device_name)[:64],
                    now,
                ),
            )
        return {
            "user": self.user(user_id),
            "session_id": session_id,
            "access_token": access,
            "access_expires_at": access_expiry,
            "refresh_token": refresh,
            "refresh_expires_at": refresh_expiry,
        }

    def authenticate(self, access_token: str) -> dict:
        row = self.store.one(
            "SELECT s.session_id,s.user_id,s.access_expires_at,u.handle,u.display_name,u.user_type,u.status,u.revision "
            "FROM sessions s JOIN users u ON u.user_id=s.user_id "
            "WHERE s.access_hash=? AND s.revoked_at IS NULL",
            (token_hash(access_token),),
        )
        if row is None or row["access_expires_at"] <= self.clock() or row["status"] != "active":
            raise ServiceError(401, "session_expired", "A sessão expirou.")
        return dict(row)

    def refresh(self, refresh_token: str, device_name: str = "Groundfire") -> dict:
        hashed = token_hash(refresh_token)
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            row = db.execute("SELECT * FROM sessions WHERE refresh_hash=? AND revoked_at IS NULL", (hashed,)).fetchone()
            if row is None or row["refresh_expires_at"] <= now:
                raise ServiceError(401, "session_expired", "A sessão expirou.")
            db.execute("UPDATE sessions SET revoked_at=? WHERE session_id=?", (now, row["session_id"]))
        return self._create_session(row["user_id"], device_name)

    def logout(self, session_id: str, user_id: str) -> None:
        with self.store.transaction(immediate=True) as db:
            db.execute(
                "UPDATE sessions SET revoked_at=? WHERE session_id=? AND user_id=?", (self.clock(), session_id, user_id)
            )

    def user(self, user_id: str) -> dict:
        row = self.store.one(
            "SELECT user_id,handle,display_name,user_type,status,revision,created_at FROM users WHERE user_id=?",
            (user_id,),
        )
        if row is None:
            raise not_found()
        return dict(row)

    def update_presence(self, user_id: str, availability: str) -> dict:
        if availability not in {"online", "away", "invisible"}:
            raise bad_request("invalid_presence", "Presença inválida.")
        now = self.clock()
        expiry = now + self.settings.presence_ttl_seconds
        with self.store.transaction(immediate=True) as db:
            db.execute(
                "INSERT INTO presence(user_id,availability,expires_at,updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET availability=excluded.availability,expires_at=excluded.expires_at,updated_at=excluded.updated_at",
                (user_id, availability, expiry, now),
            )
            recipients = self._friend_ids(db, user_id)
            self.store.emit(
                db, recipients, "presence.changed", user_id, None, {"user_id": user_id, "availability": availability}
            )
        return {"availability": availability, "expires_at": expiry}

    def request_friend(self, user_id: str, target_id: str) -> dict:
        if user_id == target_id:
            raise bad_request("invalid_target", "Não é possível adicionar a própria conta.")
        now = self.clock()
        request_id = new_id("frq")
        with self.store.transaction(immediate=True) as db:
            self._require_account(db, user_id)
            self._require_account(db, target_id)
            if self._is_blocked(db, user_id, target_id):
                raise not_found()
            pair = sorted((user_id, target_id))
            if db.execute("SELECT 1 FROM friendships WHERE user_low=? AND user_high=?", pair).fetchone():
                raise conflict("already_friends", "Os usuários já são amigos.")
            existing = db.execute(
                "SELECT * FROM friend_requests WHERE sender_id=? AND recipient_id=? AND state='pending'",
                (user_id, target_id),
            ).fetchone()
            if existing:
                return dict(existing)
            reverse = db.execute(
                "SELECT request_id FROM friend_requests WHERE sender_id=? AND recipient_id=? AND state='pending'",
                (target_id, user_id),
            ).fetchone()
            if reverse:
                return self._accept_friend_in_transaction(db, user_id, reverse["request_id"])
            db.execute(
                "INSERT INTO friend_requests(request_id,sender_id,recipient_id,state,created_at) VALUES(?,?,?,?,?)",
                (request_id, user_id, target_id, "pending", now),
            )
            self.store.emit(
                db,
                [target_id],
                "friend_request.created",
                request_id,
                1,
                {"request_id": request_id, "sender_id": user_id},
            )
        return {
            "request_id": request_id,
            "sender_id": user_id,
            "recipient_id": target_id,
            "state": "pending",
            "created_at": now,
        }

    def accept_friend(self, user_id: str, request_id: str) -> dict:
        with self.store.transaction(immediate=True) as db:
            return self._accept_friend_in_transaction(db, user_id, request_id)

    def _accept_friend_in_transaction(self, db: sqlite3.Connection, user_id: str, request_id: str) -> dict:
        row = db.execute(
            "SELECT * FROM friend_requests WHERE request_id=? AND state='pending'", (request_id,)
        ).fetchone()
        if row is None or row["recipient_id"] != user_id:
            raise not_found()
        if self._is_blocked(db, row["sender_id"], row["recipient_id"]):
            raise not_found()
        pair = sorted((row["sender_id"], row["recipient_id"]))
        db.execute("UPDATE friend_requests SET state='accepted' WHERE request_id=?", (request_id,))
        db.execute(
            "INSERT OR IGNORE INTO friendships(user_low,user_high,created_at) VALUES(?,?,?)", (*pair, self.clock())
        )
        data = {"user_ids": pair, "state": "friends"}
        self.store.emit(db, pair, "friendship.changed", request_id, 1, data)
        return data

    def list_friends(self, user_id: str) -> list[dict]:
        now = self.clock()
        rows = self.store.all(
            "SELECT u.user_id,u.handle,u.display_name,u.user_type,p.availability,p.expires_at "
            "FROM friendships f JOIN users u ON u.user_id=CASE WHEN f.user_low=? THEN f.user_high ELSE f.user_low END "
            "LEFT JOIN presence p ON p.user_id=u.user_id WHERE f.user_low=? OR f.user_high=? ORDER BY u.display_name,u.user_id",
            (user_id, user_id, user_id),
        )
        result = []
        for row in rows:
            item = dict(row)
            if not item["expires_at"] or item["expires_at"] <= now or item["availability"] == "invisible":
                item["availability"] = "offline"
            item.pop("expires_at", None)
            result.append(item)
        return result

    def block(self, user_id: str, target_id: str) -> None:
        if user_id == target_id:
            raise bad_request("invalid_target", "Não é possível bloquear a própria conta.")
        pair = sorted((user_id, target_id))
        with self.store.transaction(immediate=True) as db:
            self._require_user(db, target_id)
            db.execute(
                "INSERT OR IGNORE INTO blocks(blocker_id,blocked_id,created_at) VALUES(?,?,?)",
                (user_id, target_id, self.clock()),
            )
            db.execute("DELETE FROM friendships WHERE user_low=? AND user_high=?", pair)
            db.execute(
                "UPDATE friend_requests SET state='cancelled' WHERE state='pending' AND ((sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?))",
                (user_id, target_id, target_id, user_id),
            )
            db.execute(
                "UPDATE invites SET revoked_at=? WHERE revoked_at IS NULL AND ((sender_id=? AND recipient_id=?) OR (sender_id=? AND recipient_id=?))",
                (self.clock(), user_id, target_id, target_id, user_id),
            )

    def create_party(self, user_id: str) -> dict:
        party_id = new_id("pty")
        now = self.clock()
        try:
            with self.store.transaction(immediate=True) as db:
                db.execute("INSERT INTO parties(party_id,leader_id,created_at) VALUES(?,?,?)", (party_id, user_id, now))
                db.execute(
                    "INSERT INTO party_members(party_id,user_id,joined_at) VALUES(?,?,?)", (party_id, user_id, now)
                )
                self.store.emit(db, [user_id], "party.changed", party_id, 1, {"party_id": party_id, "revision": 1})
        except sqlite3.IntegrityError as exc:
            raise conflict("already_in_party", "O usuário já participa de um grupo.") from exc
        return self.party(user_id, party_id)

    def party(self, user_id: str, party_id: str) -> dict:
        row = self.store.one("SELECT * FROM parties WHERE party_id=?", (party_id,))
        if row is None or not self.store.one(
            "SELECT 1 FROM party_members WHERE party_id=? AND user_id=?", (party_id, user_id)
        ):
            raise not_found()
        members = [
            dict(item)
            for item in self.store.all(
                "SELECT pm.user_id,u.display_name,pm.joined_at,pm.ready_revision FROM party_members pm JOIN users u ON u.user_id=pm.user_id WHERE pm.party_id=? ORDER BY pm.joined_at,pm.user_id",
                (party_id,),
            )
        ]
        result = dict(row)
        result["members"] = members
        return result

    def leave_party(self, user_id: str, party_id: str) -> None:
        with self.store.transaction(immediate=True) as db:
            party = db.execute("SELECT * FROM parties WHERE party_id=?", (party_id,)).fetchone()
            membership = db.execute(
                "SELECT 1 FROM party_members WHERE party_id=? AND user_id=?", (party_id, user_id)
            ).fetchone()
            if party is None or membership is None:
                raise not_found()
            db.execute("DELETE FROM party_members WHERE party_id=? AND user_id=?", (party_id, user_id))
            members = db.execute(
                "SELECT user_id FROM party_members WHERE party_id=? ORDER BY joined_at,user_id", (party_id,)
            ).fetchall()
            if not members:
                db.execute("DELETE FROM parties WHERE party_id=?", (party_id,))
                return
            leader = party["leader_id"]
            if leader == user_id:
                leader = members[0]["user_id"]
            revision = party["revision"] + 1
            db.execute("UPDATE parties SET leader_id=?,revision=? WHERE party_id=?", (leader, revision, party_id))
            db.execute("UPDATE party_members SET ready_revision=NULL WHERE party_id=?", (party_id,))
            db.execute(
                "UPDATE queue_tickets SET state='cancelled' WHERE party_id=? AND state IN ('searching','reserved')",
                (party_id,),
            )
            self.store.emit(
                db,
                [r["user_id"] for r in members],
                "party.changed",
                party_id,
                revision,
                {"party_id": party_id, "revision": revision, "leader_id": leader},
            )

    def set_party_ready(self, user_id: str, party_id: str, revision: int, ready: bool) -> dict:
        with self.store.transaction(immediate=True) as db:
            party = db.execute("SELECT * FROM parties WHERE party_id=?", (party_id,)).fetchone()
            if party is None or party["revision"] != revision:
                raise conflict("party_changed", "O grupo foi alterado; confirme novamente.")
            changed = db.execute(
                "UPDATE party_members SET ready_revision=? WHERE party_id=? AND user_id=?",
                (revision if ready else None, party_id, user_id),
            ).rowcount
            if not changed:
                raise not_found()
            members = [
                r["user_id"] for r in db.execute("SELECT user_id FROM party_members WHERE party_id=?", (party_id,))
            ]
            self.store.emit(
                db,
                members,
                "party.changed",
                party_id,
                revision,
                {"party_id": party_id, "user_id": user_id, "ready": ready},
            )
        return self.party(user_id, party_id)

    def create_lobby(self, user_id: str, payload: dict) -> dict:
        rules = self._validate_lobby(payload)
        lobby_id = new_id("lob")
        now = self.clock()
        password = str(payload.get("password", ""))
        encoded = hash_password(password) if password else None
        try:
            with self.store.transaction(immediate=True) as db:
                db.execute(
                    "INSERT INTO lobbies(lobby_id,name,leader_id,visibility,password_hash,capacity,rounds,map_id,seed,bots,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        lobby_id,
                        rules["name"],
                        user_id,
                        rules["visibility"],
                        encoded,
                        rules["capacity"],
                        rules["rounds"],
                        rules["map_id"],
                        rules["seed"],
                        rules["bots"],
                        now,
                    ),
                )
                db.execute(
                    "INSERT INTO lobby_members(lobby_id,user_id,joined_at) VALUES(?,?,?)", (lobby_id, user_id, now)
                )
                self.store.emit(db, [user_id], "lobby.changed", lobby_id, 1, {"lobby_id": lobby_id, "revision": 1})
        except sqlite3.IntegrityError as exc:
            raise conflict("already_in_lobby", "O usuário já participa de uma sala.") from exc
        return self.lobby(user_id, lobby_id)

    def _validate_lobby(self, payload: dict) -> dict:
        try:
            name = validate_display_name(str(payload.get("name", "Groundfire")))
            capacity = int(payload.get("capacity", 8))
            rounds = int(payload.get("rounds", 10))
            bots = int(payload.get("bots", 0))
            seed = int(payload.get("seed", 1))
        except (ValueError, TypeError) as exc:
            raise bad_request("invalid_rules", "As regras da sala são inválidas.") from exc
        visibility = str(payload.get("visibility", "public"))
        map_id = str(payload.get("map_id", "classic"))
        if visibility not in {"public", "private"} or map_id not in {"classic", "basin", "ridge", "crater", "mesa"}:
            raise bad_request("invalid_rules", "Visibilidade ou mapa inválido.")
        if not 2 <= capacity <= 8 or not 5 <= rounds <= 50 or not 0 <= bots < capacity:
            raise bad_request("invalid_rules", "Capacidade, rodadas ou bots fora do limite.")
        return {
            "name": name,
            "capacity": capacity,
            "rounds": rounds,
            "bots": bots,
            "seed": seed,
            "visibility": visibility,
            "map_id": map_id,
        }

    def lobby(self, user_id: str | None, lobby_id: str) -> dict:
        row = self.store.one("SELECT * FROM lobbies WHERE lobby_id=?", (lobby_id,))
        if row is None:
            raise not_found()
        is_member = bool(
            user_id
            and self.store.one("SELECT 1 FROM lobby_members WHERE lobby_id=? AND user_id=?", (lobby_id, user_id))
        )
        if row["visibility"] != "public" and not is_member:
            raise not_found()
        result = {key: row[key] for key in row.keys() if key != "password_hash"}
        result["passworded"] = bool(row["password_hash"])
        result["members"] = [
            dict(member)
            for member in self.store.all(
                "SELECT lm.user_id,u.display_name,lm.role,lm.ready_revision,lm.joined_at FROM lobby_members lm JOIN users u ON u.user_id=lm.user_id WHERE lm.lobby_id=? ORDER BY lm.joined_at,lm.user_id",
                (lobby_id,),
            )
        ]
        return result

    def list_lobbies(self) -> list[dict]:
        rows = self.store.all(
            "SELECT l.lobby_id,l.name,l.capacity,l.rounds,l.map_id,l.seed,l.bots,l.revision,l.state,(l.password_hash IS NOT NULL) passworded,COUNT(lm.user_id) players "
            "FROM lobbies l LEFT JOIN lobby_members lm ON lm.lobby_id=l.lobby_id WHERE l.visibility='public' AND l.state='open' GROUP BY l.lobby_id ORDER BY l.created_at,l.lobby_id"
        )
        return [dict(row) for row in rows]

    def list_servers(self) -> list[dict]:
        servers = []
        for lobby in self.list_lobbies():
            servers.append(
                {
                    "server_id": lobby["lobby_id"],
                    "name": lobby["name"],
                    "managed": True,
                    "status": "available",
                    "region": "world",
                    "map_id": lobby["map_id"],
                    "rules": {"rounds": lobby["rounds"], "max_players": lobby["capacity"]},
                    "occupancy": {
                        "players": lobby["players"],
                        "bots": lobby["bots"],
                        "reserved": self._reserved_count(lobby["lobby_id"]),
                        "spectators": 0,
                    },
                    "passworded": bool(lobby["passworded"]),
                    "runtime_version": "groundfire-0.25",
                    "join_in_progress": False,
                    "transports": [
                        {
                            "kind": "wss",
                            "protocol_version": 3,
                            "tls": self.settings.public_base_url.startswith("https://"),
                            "admission_required": True,
                        }
                    ],
                    "revision": lobby["revision"],
                }
            )
        return servers

    def _reserved_count(self, lobby_id: str) -> int:
        row = self.store.one(
            "SELECT COUNT(*) count FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE r.lobby_id=? AND r.state IN ('held','accepted','preparing') AND r.expires_at>?",
            (lobby_id, self.clock()),
        )
        return int(row["count"] if row else 0)

    def join_lobby(self, user_id: str, lobby_id: str, password: str = "", role: str = "player") -> dict:
        if role not in {"player", "spectator"}:
            raise bad_request("invalid_role", "Papel inválido.")
        with self.store.transaction(immediate=True) as db:
            row = db.execute("SELECT * FROM lobbies WHERE lobby_id=?", (lobby_id,)).fetchone()
            if row is None or row["state"] != "open":
                raise not_found()
            if row["password_hash"] and not verify_password(row["password_hash"], password):
                raise ServiceError(403, "invalid_password", "Senha incorreta.")
            if db.execute("SELECT 1 FROM lobby_members WHERE lobby_id=? AND user_id=?", (lobby_id, user_id)).fetchone():
                return self.lobby(user_id, lobby_id)
            if db.execute("SELECT 1 FROM lobby_members WHERE user_id=?", (user_id,)).fetchone():
                raise conflict("already_in_lobby", "Saia da sala atual antes de entrar em outra.")
            players = db.execute(
                "SELECT COUNT(*) FROM lobby_members WHERE lobby_id=? AND role='player'", (lobby_id,)
            ).fetchone()[0]
            reserved = db.execute(
                "SELECT COUNT(*) FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE r.lobby_id=? AND r.state IN ('held','accepted','preparing') AND r.expires_at>?",
                (lobby_id, self.clock()),
            ).fetchone()[0]
            if role == "player" and players + row["bots"] + reserved >= row["capacity"]:
                raise conflict(
                    "server_full",
                    "A sala está cheia.",
                    retryable=True,
                    available_slots=max(0, row["capacity"] - players - row["bots"] - reserved),
                )
            revision = row["revision"] + 1
            db.execute(
                "INSERT INTO lobby_members(lobby_id,user_id,role,joined_at) VALUES(?,?,?,?)",
                (lobby_id, user_id, role, self.clock()),
            )
            db.execute("UPDATE lobbies SET revision=? WHERE lobby_id=?", (revision, lobby_id))
            db.execute("UPDATE lobby_members SET ready_revision=NULL WHERE lobby_id=?", (lobby_id,))
            members = [
                r["user_id"] for r in db.execute("SELECT user_id FROM lobby_members WHERE lobby_id=?", (lobby_id,))
            ]
            self.store.emit(
                db,
                members,
                "lobby.changed",
                lobby_id,
                revision,
                {"lobby_id": lobby_id, "revision": revision, "joined_user_id": user_id},
            )
        return self.lobby(user_id, lobby_id)

    def set_lobby_ready(self, user_id: str, lobby_id: str, revision: int, ready: bool) -> dict:
        with self.store.transaction(immediate=True) as db:
            lobby = db.execute("SELECT revision FROM lobbies WHERE lobby_id=?", (lobby_id,)).fetchone()
            if lobby is None:
                raise not_found()
            if lobby["revision"] != revision:
                raise conflict("revision_conflict", "A sala foi alterada.")
            membership = db.execute(
                "SELECT role FROM lobby_members WHERE lobby_id=? AND user_id=?", (lobby_id, user_id)
            ).fetchone()
            if membership is None:
                raise not_found()
            if membership["role"] != "player":
                raise forbidden("spectator_forbidden", "Espectadores não marcam pronto.")
            db.execute(
                "UPDATE lobby_members SET ready_revision=? WHERE lobby_id=? AND user_id=?",
                (revision if ready else None, lobby_id, user_id),
            )
            members = [
                r["user_id"] for r in db.execute("SELECT user_id FROM lobby_members WHERE lobby_id=?", (lobby_id,))
            ]
            self.store.emit(
                db,
                members,
                "lobby.changed",
                lobby_id,
                revision,
                {"lobby_id": lobby_id, "user_id": user_id, "ready": ready},
            )
        return self.lobby(user_id, lobby_id)

    def leave_lobby(self, user_id: str, lobby_id: str) -> None:
        with self.store.transaction(immediate=True) as db:
            lobby = db.execute("SELECT * FROM lobbies WHERE lobby_id=?", (lobby_id,)).fetchone()
            membership = db.execute(
                "SELECT 1 FROM lobby_members WHERE lobby_id=? AND user_id=?", (lobby_id, user_id)
            ).fetchone()
            if lobby is None or membership is None:
                raise not_found()
            db.execute("DELETE FROM lobby_members WHERE lobby_id=? AND user_id=?", (lobby_id, user_id))
            members = db.execute(
                "SELECT user_id FROM lobby_members WHERE lobby_id=? ORDER BY joined_at,user_id", (lobby_id,)
            ).fetchall()
            if not members:
                db.execute("DELETE FROM lobbies WHERE lobby_id=?", (lobby_id,))
                return
            leader = lobby["leader_id"] if lobby["leader_id"] != user_id else members[0]["user_id"]
            revision = lobby["revision"] + 1
            db.execute("UPDATE lobbies SET leader_id=?,revision=? WHERE lobby_id=?", (leader, revision, lobby_id))
            db.execute("UPDATE lobby_members SET ready_revision=NULL WHERE lobby_id=?", (lobby_id,))
            self.store.emit(
                db,
                [r["user_id"] for r in members],
                "lobby.changed",
                lobby_id,
                revision,
                {"lobby_id": lobby_id, "leader_id": leader, "left_user_id": user_id},
            )

    def create_invite(
        self, user_id: str, target_type: str, target_id: str, recipient_id: str | None = None, max_uses: int = 1
    ) -> dict:
        if target_type not in {"party", "lobby"} or not 1 <= max_uses <= 8:
            raise bad_request("invalid_invite", "Convite inválido.")
        secret = new_secret(9)
        invite_id = new_id("inv")
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            if target_type == "party":
                target = db.execute("SELECT leader_id FROM parties WHERE party_id=?", (target_id,)).fetchone()
            else:
                target = db.execute("SELECT leader_id FROM lobbies WHERE lobby_id=?", (target_id,)).fetchone()
            if target is None or target["leader_id"] != user_id:
                raise forbidden()
            if recipient_id:
                self._require_user(db, recipient_id)
                if self._is_blocked(db, user_id, recipient_id):
                    raise not_found()
            expires = now + self.settings.invite_ttl_seconds
            db.execute(
                "INSERT INTO invites(invite_id,code_hash,sender_id,recipient_id,target_type,target_id,max_uses,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (invite_id, token_hash(secret), user_id, recipient_id, target_type, target_id, max_uses, expires, now),
            )
            if recipient_id:
                self.store.emit(
                    db,
                    [recipient_id],
                    "invite.created",
                    invite_id,
                    1,
                    {"invite_id": invite_id, "target_type": target_type, "target_id": target_id, "sender_id": user_id},
                )
        return {
            "invite_id": invite_id,
            "code": secret,
            "target_type": target_type,
            "target_id": target_id,
            "recipient_id": recipient_id,
            "expires_at": expires,
            "max_uses": max_uses,
        }

    def accept_invite(
        self, user_id: str, *, invite_id: str | None = None, code: str | None = None, password: str = ""
    ) -> dict:
        if not invite_id and not code:
            raise bad_request("invalid_invite", "Informe o convite ou código.")
        with self.store.transaction(immediate=True) as db:
            if invite_id:
                invite = db.execute("SELECT * FROM invites WHERE invite_id=?", (invite_id,)).fetchone()
            else:
                invite = db.execute("SELECT * FROM invites WHERE code_hash=?", (token_hash(str(code)),)).fetchone()
            if (
                invite is None
                or invite["revoked_at"] is not None
                or invite["expires_at"] <= self.clock()
                or invite["use_count"] >= invite["max_uses"]
            ):
                raise ServiceError(410, "resource_expired", "Convite inválido ou expirado.")
            if invite["recipient_id"] and invite["recipient_id"] != user_id:
                raise not_found()
            if self._is_blocked(db, invite["sender_id"], user_id):
                raise not_found()
            db.execute("UPDATE invites SET use_count=use_count+1 WHERE invite_id=?", (invite["invite_id"],))
            target_type, target_id = invite["target_type"], invite["target_id"]
        if target_type == "lobby":
            data = self.join_lobby(user_id, target_id, password=password)
        else:
            data = self._join_party(user_id, target_id)
        return {"target_type": target_type, "target": data}

    def _join_party(self, user_id: str, party_id: str) -> dict:
        with self.store.transaction(immediate=True) as db:
            party = db.execute("SELECT * FROM parties WHERE party_id=?", (party_id,)).fetchone()
            if party is None:
                raise not_found()
            count = db.execute("SELECT COUNT(*) FROM party_members WHERE party_id=?", (party_id,)).fetchone()[0]
            if count >= 8:
                raise conflict("party_full", "O grupo está cheio.")
            try:
                db.execute(
                    "INSERT INTO party_members(party_id,user_id,joined_at) VALUES(?,?,?)",
                    (party_id, user_id, self.clock()),
                )
            except sqlite3.IntegrityError as exc:
                raise conflict("already_in_party", "O usuário já participa de um grupo.") from exc
            revision = party["revision"] + 1
            db.execute("UPDATE parties SET revision=? WHERE party_id=?", (revision, party_id))
            db.execute("UPDATE party_members SET ready_revision=NULL WHERE party_id=?", (party_id,))
            members = [
                r["user_id"] for r in db.execute("SELECT user_id FROM party_members WHERE party_id=?", (party_id,))
            ]
            self.store.emit(
                db,
                members,
                "party.changed",
                party_id,
                revision,
                {"party_id": party_id, "revision": revision, "joined_user_id": user_id},
            )
        return self.party(user_id, party_id)

    def queue(self, user_id: str, payload: dict) -> dict:
        party_id = payload.get("party_id")
        criteria = dict(payload.get("criteria") or {})
        members = [user_id]
        party_revision = None
        with self.store.transaction(immediate=True) as db:
            if party_id:
                party = db.execute("SELECT * FROM parties WHERE party_id=?", (party_id,)).fetchone()
                if party is None or party["leader_id"] != user_id:
                    raise forbidden()
                party_revision = int(payload.get("party_revision", -1))
                if party_revision != party["revision"]:
                    raise conflict("party_changed", "O grupo foi alterado.")
                party_members = db.execute(
                    "SELECT user_id,ready_revision FROM party_members WHERE party_id=?", (party_id,)
                ).fetchall()
                if any(row["ready_revision"] != party_revision for row in party_members):
                    raise conflict("party_not_ready", "Todos os membros precisam confirmar a busca.")
                members = [row["user_id"] for row in party_members]
            active = db.execute(
                "SELECT 1 FROM queue_tickets WHERE (owner_id=? OR party_id=?) AND state IN ('searching','reserved','preparing') AND expires_at>?",
                (user_id, party_id, self.clock()),
            ).fetchone()
            if active:
                raise conflict("already_queued", "Já existe uma busca ativa.")
            queue_id = new_id("que")
            expires = self.clock() + self.settings.queue_ttl_seconds
            db.execute(
                "INSERT INTO queue_tickets(queue_id,owner_id,party_id,party_revision,criteria_json,state,expires_at,created_at) VALUES(?,?,?,?,?,'searching',?,?)",
                (queue_id, user_id, party_id, party_revision, json.dumps(criteria), expires, self.clock()),
            )
            reservation = self._find_and_reserve(db, members, criteria)
            if reservation:
                db.execute(
                    "UPDATE queue_tickets SET state='reserved',reservation_id=? WHERE queue_id=?",
                    (reservation["reservation_id"], queue_id),
                )
            self.store.emit(
                db,
                members,
                "queue.changed",
                queue_id,
                1,
                {
                    "queue_id": queue_id,
                    "state": "reserved" if reservation else "searching",
                    "reservation_id": reservation["reservation_id"] if reservation else None,
                },
            )
        return self.queue_status(user_id, queue_id)

    def reserve_server(self, user_id: str, lobby_id: str, *, password: str = "") -> dict:
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            lobby = db.execute("SELECT * FROM lobbies WHERE lobby_id=? AND state='open'", (lobby_id,)).fetchone()
            if lobby is None:
                raise not_found()
            if lobby["password_hash"] and not verify_password(lobby["password_hash"], password):
                raise ServiceError(403, "invalid_password", "Senha incorreta.")
            players = db.execute(
                "SELECT COUNT(*) FROM lobby_members WHERE lobby_id=? AND role='player'", (lobby_id,)
            ).fetchone()[0]
            reserved = db.execute(
                "SELECT COUNT(*) FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE r.lobby_id=? AND r.state IN ('held','accepted','preparing') AND r.expires_at>?",
                (lobby_id, now),
            ).fetchone()[0]
            if players + lobby["bots"] + reserved >= lobby["capacity"]:
                raise conflict("server_full", "A sala está cheia.", retryable=True, available_slots=0)
            reservation_id = new_id("res")
            expiry = now + self.settings.reservation_ttl_seconds
            db.execute(
                "INSERT INTO reservations(reservation_id,lobby_id,state,expires_at,created_at) VALUES(?,?,'held',?,?)",
                (reservation_id, lobby_id, expiry, now),
            )
            db.execute("INSERT INTO reservation_members(reservation_id,user_id) VALUES(?,?)", (reservation_id, user_id))
            self.store.emit(
                db,
                [user_id],
                "reservation.changed",
                reservation_id,
                1,
                {"reservation_id": reservation_id, "state": "held", "lobby_id": lobby_id},
            )
        return self.reservation(user_id, reservation_id)

    def _find_and_reserve(self, db: sqlite3.Connection, members: list[str], criteria: dict) -> dict | None:
        lobby_id = criteria.get("target_lobby_id")
        query = "SELECT * FROM lobbies WHERE state='open' AND visibility='public' AND password_hash IS NULL"
        params: list[Any] = []
        if lobby_id:
            query += " AND lobby_id=?"
            params.append(lobby_id)
        if criteria.get("map_id"):
            query += " AND map_id=?"
            params.append(str(criteria["map_id"]))
        query += " ORDER BY created_at,lobby_id"
        for lobby in db.execute(query, tuple(params)).fetchall():
            players = db.execute(
                "SELECT COUNT(*) FROM lobby_members WHERE lobby_id=? AND role='player'", (lobby["lobby_id"],)
            ).fetchone()[0]
            reserved = db.execute(
                "SELECT COUNT(*) FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE r.lobby_id=? AND r.state IN ('held','accepted','preparing') AND r.expires_at>?",
                (lobby["lobby_id"], self.clock()),
            ).fetchone()[0]
            available = lobby["capacity"] - lobby["bots"] - players - reserved
            if available < len(members):
                continue
            reservation_id = new_id("res")
            expires = self.clock() + self.settings.reservation_ttl_seconds
            db.execute(
                "INSERT INTO reservations(reservation_id,lobby_id,state,expires_at,created_at) VALUES(?,?,'held',?,?)",
                (reservation_id, lobby["lobby_id"], expires, self.clock()),
            )
            db.executemany(
                "INSERT INTO reservation_members(reservation_id,user_id) VALUES(?,?)",
                [(reservation_id, member) for member in members],
            )
            return {"reservation_id": reservation_id, "lobby_id": lobby["lobby_id"], "expires_at": expires}
        return None

    def queue_status(self, user_id: str, queue_id: str) -> dict:
        row = self.store.one("SELECT * FROM queue_tickets WHERE queue_id=?", (queue_id,))
        if row is None:
            raise not_found()
        allowed = row["owner_id"] == user_id or (
            row["party_id"]
            and self.store.one("SELECT 1 FROM party_members WHERE party_id=? AND user_id=?", (row["party_id"], user_id))
        )
        if not allowed:
            raise not_found()
        result = dict(row)
        result["criteria"] = json.loads(result.pop("criteria_json"))
        return result

    def cancel_queue(self, user_id: str, queue_id: str) -> None:
        with self.store.transaction(immediate=True) as db:
            row = db.execute("SELECT * FROM queue_tickets WHERE queue_id=?", (queue_id,)).fetchone()
            if row is None:
                raise not_found()
            allowed = row["owner_id"] == user_id or (
                row["party_id"]
                and db.execute(
                    "SELECT 1 FROM party_members WHERE party_id=? AND user_id=?", (row["party_id"], user_id)
                ).fetchone()
            )
            if not allowed:
                raise not_found()
            if row["state"] in {"matched", "cancelled", "expired", "failed"}:
                return
            db.execute("UPDATE queue_tickets SET state='cancelled' WHERE queue_id=?", (queue_id,))
            if row["reservation_id"]:
                db.execute(
                    "UPDATE reservations SET state='cancelled' WHERE reservation_id=? AND state IN ('held','accepted','preparing')",
                    (row["reservation_id"],),
                )
            members = [row["owner_id"]]
            if row["party_id"]:
                members = [
                    r["user_id"]
                    for r in db.execute("SELECT user_id FROM party_members WHERE party_id=?", (row["party_id"],))
                ]
            self.store.emit(db, members, "queue.changed", queue_id, 1, {"queue_id": queue_id, "state": "cancelled"})

    def reservation(self, user_id: str, reservation_id: str) -> dict:
        row = self.store.one("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,))
        membership = self.store.one(
            "SELECT * FROM reservation_members WHERE reservation_id=? AND user_id=?", (reservation_id, user_id)
        )
        if row is None or membership is None:
            raise not_found()
        result = dict(row)
        result["members"] = [
            dict(member)
            for member in self.store.all(
                "SELECT user_id,accepted,(admission_hash IS NOT NULL) ticket_issued,(admission_used_at IS NOT NULL) ticket_used FROM reservation_members WHERE reservation_id=? ORDER BY user_id",
                (reservation_id,),
            )
        ]
        return result

    def accept_reservation(self, user_id: str, reservation_id: str) -> dict:
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            reservation = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            if (
                reservation is None
                or reservation["expires_at"] <= now
                or reservation["state"] not in {"held", "accepted"}
            ):
                raise conflict("reservation_expired", "A reserva expirou.")
            changed = db.execute(
                "UPDATE reservation_members SET accepted=1 WHERE reservation_id=? AND user_id=?",
                (reservation_id, user_id),
            ).rowcount
            if not changed:
                raise not_found()
            members = db.execute(
                "SELECT user_id,accepted FROM reservation_members WHERE reservation_id=?", (reservation_id,)
            ).fetchall()
            state = "accepted" if all(row["accepted"] for row in members) else "held"
            db.execute("UPDATE reservations SET state=? WHERE reservation_id=?", (state, reservation_id))
            self.store.emit(
                db,
                [r["user_id"] for r in members],
                "reservation.changed",
                reservation_id,
                1,
                {"reservation_id": reservation_id, "state": state, "accepted_user_id": user_id},
            )
        return self.reservation(user_id, reservation_id)

    def start_lobby(self, user_id: str, lobby_id: str, revision: int) -> dict:
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            lobby = db.execute("SELECT * FROM lobbies WHERE lobby_id=?", (lobby_id,)).fetchone()
            if lobby is None:
                raise not_found()
            if lobby["leader_id"] != user_id:
                raise forbidden()
            if lobby["state"] in {"allocating", "in_match"} and lobby["match_id"]:
                match = db.execute("SELECT * FROM matches WHERE match_id=?", (lobby["match_id"],)).fetchone()
                if match is not None:
                    return self._match_payload(match, lobby, include_secret=True)
            if lobby["state"] != "open":
                raise conflict("lobby_not_open", "A sala não está disponível para iniciar.")
            if lobby["revision"] != revision:
                raise conflict("lobby_changed", "A sala foi alterada.", current_revision=lobby["revision"])
            members = db.execute(
                "SELECT user_id,ready_revision FROM lobby_members WHERE lobby_id=? AND role='player' ORDER BY joined_at,user_id",
                (lobby_id,),
            ).fetchall()
            if len(members) + lobby["bots"] < 2:
                raise conflict("not_enough_players", "São necessários pelo menos dois participantes.")
            if any(member["ready_revision"] != revision for member in members):
                raise conflict("lobby_not_ready", "Todos os jogadores precisam confirmar que estão prontos.")
            reservation_id = new_id("res")
            expires = now + self.settings.reservation_ttl_seconds
            db.execute(
                "INSERT INTO reservations(reservation_id,lobby_id,state,expires_at,created_at) VALUES(?,?,'accepted',?,?)",
                (reservation_id, lobby_id, expires, now),
            )
            db.executemany(
                "INSERT INTO reservation_members(reservation_id,user_id,accepted) VALUES(?,?,1)",
                [(reservation_id, member["user_id"]) for member in members],
            )
        return self.prepare_allocation(reservation_id)

    def prepare_allocation(self, reservation_id: str) -> dict:
        with self.store.transaction(immediate=True) as db:
            reservation = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            if reservation is None:
                raise not_found()
            if reservation["expires_at"] <= self.clock() or reservation["state"] not in {"accepted", "preparing"}:
                raise conflict("reservation_not_ready", "A reserva não está pronta para alocação.")
            existing = db.execute("SELECT * FROM matches WHERE reservation_id=?", (reservation_id,)).fetchone()
            lobby = db.execute("SELECT * FROM lobbies WHERE lobby_id=?", (reservation["lobby_id"],)).fetchone()
            if lobby is None:
                raise not_found()
            if existing is not None:
                return self._match_payload(existing, lobby, include_secret=True)
            active = db.execute("SELECT COUNT(*) FROM matches WHERE state IN ('allocating','active')").fetchone()[0]
            if active >= self.settings.max_workers:
                raise ServiceError(503, "capacity_unavailable", "Não há worker disponível agora.", retryable=True)
            match_id = new_id("mat")
            secret = new_secret(32)
            db.execute(
                "INSERT INTO matches(match_id,lobby_id,reservation_id,state,runtime_version,session_secret,created_at) "
                "VALUES(?,?,?,'allocating','groundfire-headless-0.25',?,?)",
                (match_id, lobby["lobby_id"], reservation_id, secret, self.clock()),
            )
            db.execute("UPDATE reservations SET state='preparing' WHERE reservation_id=?", (reservation_id,))
            db.execute(
                "UPDATE lobbies SET state='allocating',match_id=? WHERE lobby_id=?", (match_id, lobby["lobby_id"])
            )
            row = db.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
            users = [
                item["user_id"]
                for item in db.execute(
                    "SELECT user_id FROM reservation_members WHERE reservation_id=?", (reservation_id,)
                )
            ]
            self.store.emit(
                db,
                users,
                "match.allocating",
                match_id,
                1,
                {"match_id": match_id, "lobby_id": lobby["lobby_id"], "reservation_id": reservation_id},
            )
            return self._match_payload(row, lobby, include_secret=True)

    def activate_match(self, match_id: str, allocation: dict) -> dict:
        with self.store.transaction(immediate=True) as db:
            match = db.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
            if match is None:
                raise not_found()
            db.execute(
                "UPDATE matches SET state='active',udp_host=?,udp_port=?,websocket_url=?,worker_pid=?,gateway_pid=?,started_at=? "
                "WHERE match_id=?",
                (
                    allocation["udp_host"],
                    allocation["udp_port"],
                    allocation["websocket_url"],
                    allocation["worker_pid"],
                    allocation["gateway_pid"],
                    self.clock(),
                    match_id,
                ),
            )
            db.execute("UPDATE lobbies SET state='in_match' WHERE lobby_id=?", (match["lobby_id"],))
            users = [
                row["user_id"]
                for row in db.execute(
                    "SELECT user_id FROM reservation_members WHERE reservation_id=?", (match["reservation_id"],)
                )
            ]
            self.store.emit(
                db,
                users,
                "match.ready",
                match_id,
                1,
                {
                    "match_id": match_id,
                    "lobby_id": match["lobby_id"],
                    "reservation_id": match["reservation_id"],
                },
            )
            current = db.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
            lobby = db.execute("SELECT * FROM lobbies WHERE lobby_id=?", (match["lobby_id"],)).fetchone()
            return self._match_payload(current, lobby)

    def fail_match(self, match_id: str, code: str) -> None:
        with self.store.transaction(immediate=True) as db:
            match = db.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
            if match is None:
                return
            db.execute(
                "UPDATE matches SET state='failed',failure_code=?,stopped_at=? WHERE match_id=?",
                (code, self.clock(), match_id),
            )
            db.execute("UPDATE lobbies SET state='open',match_id=NULL WHERE lobby_id=?", (match["lobby_id"],))
            db.execute("UPDATE reservations SET state='failed' WHERE reservation_id=?", (match["reservation_id"],))

    def match(self, user_id: str, match_id: str) -> dict:
        row = self.store.one("SELECT * FROM matches WHERE match_id=?", (match_id,))
        if row is None:
            raise not_found()
        lobby = self.store.one("SELECT * FROM lobbies WHERE lobby_id=?", (row["lobby_id"],))
        member = self.store.one(
            "SELECT 1 FROM reservation_members WHERE reservation_id=? AND user_id=?",
            (row["reservation_id"], user_id),
        )
        if lobby is None or member is None:
            raise not_found()
        return self._match_payload(row, lobby)

    def admission_ticket(self, user_id: str, reservation_id: str, transport: str = "wss") -> dict:
        if transport not in {"wss", "ws"}:
            raise bad_request("invalid_transport", "Transporte inválido.")
        with self.store.transaction(immediate=True) as db:
            reservation = db.execute("SELECT * FROM reservations WHERE reservation_id=?", (reservation_id,)).fetchone()
            member = db.execute(
                "SELECT * FROM reservation_members WHERE reservation_id=? AND user_id=?", (reservation_id, user_id)
            ).fetchone()
            if reservation is None or member is None:
                raise not_found()
            if (
                reservation["expires_at"] <= self.clock()
                or reservation["state"] not in {"accepted", "preparing"}
                or not member["accepted"]
            ):
                raise conflict("reservation_not_ready", "A reserva ainda não foi aceita por todos.")
            match = db.execute(
                "SELECT * FROM matches WHERE reservation_id=? AND state='active'", (reservation_id,)
            ).fetchone()
            if match is None or not match["websocket_url"]:
                raise conflict("worker_not_ready", "O servidor da partida ainda está sendo preparado.", retryable=True)
            user = db.execute("SELECT display_name FROM users WHERE user_id=?", (user_id,)).fetchone()
            ttl = max(1, int(reservation["expires_at"] - self.clock()))
            secret = generate_join_token(match["session_secret"], user["display_name"], ttl_seconds=ttl)
            db.execute(
                "UPDATE reservation_members SET admission_hash=?,admission_used_at=NULL WHERE reservation_id=? AND user_id=?",
                (token_hash(secret), reservation_id, user_id),
            )
        protocol = 2
        return {
            "reservation_id": reservation_id,
            "lobby_id": reservation["lobby_id"],
            "role": "player",
            "transport": transport,
            "protocol_version": protocol,
            "match_id": match["match_id"],
            "endpoint": match["websocket_url"],
            "admission_ticket": secret,
            "player_name": user["display_name"],
            "expires_at": reservation["expires_at"],
        }

    @staticmethod
    def _match_payload(match: sqlite3.Row, lobby: sqlite3.Row, *, include_secret: bool = False) -> dict:
        result = {
            "match_id": match["match_id"],
            "lobby_id": match["lobby_id"],
            "reservation_id": match["reservation_id"],
            "generation": match["generation"],
            "state": match["state"],
            "runtime_version": match["runtime_version"],
            "udp_host": match["udp_host"],
            "udp_port": match["udp_port"],
            "websocket_url": match["websocket_url"],
            "failure_code": match["failure_code"],
            "name": lobby["name"],
            "rounds": lobby["rounds"],
            "seed": lobby["seed"],
            "capacity": lobby["capacity"],
            "bots": lobby["bots"],
        }
        if include_secret:
            result["session_secret"] = match["session_secret"]
        return result

    def redeem_admission(self, ticket: str) -> dict:
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            row = db.execute(
                "SELECT rm.*,r.lobby_id,r.state,r.expires_at FROM reservation_members rm JOIN reservations r ON r.reservation_id=rm.reservation_id WHERE rm.admission_hash=?",
                (token_hash(ticket),),
            ).fetchone()
            if row is None or row["expires_at"] <= now or row["state"] not in {"accepted", "preparing"}:
                raise conflict("ticket_invalid", "O ticket é inválido ou expirou.")
            if row["admission_used_at"] is not None:
                raise conflict("ticket_used", "O ticket já foi usado.")
            db.execute(
                "UPDATE reservation_members SET admission_used_at=? WHERE reservation_id=? AND user_id=?",
                (now, row["reservation_id"], row["user_id"]),
            )
            db.execute("UPDATE reservations SET state='preparing' WHERE reservation_id=?", (row["reservation_id"],))
            return {
                "reservation_id": row["reservation_id"],
                "lobby_id": row["lobby_id"],
                "user_id": row["user_id"],
                "role": "player",
            }

    def events(self, user_id: str, after: int = 0, limit: int = 100) -> dict:
        rows = self.store.all(
            "SELECT sequence,event_id,event_type,resource_id,revision,data_json,created_at FROM events WHERE user_id=? AND sequence>? ORDER BY sequence LIMIT ?",
            (user_id, max(0, after), min(max(1, limit), 100)),
        )
        items = []
        for row in rows:
            item = dict(row)
            item["type"] = item.pop("event_type")
            item["data"] = json.loads(item.pop("data_json"))
            item["cursor"] = str(item["sequence"])
            items.append(item)
        return {"items": items, "next_cursor": str(items[-1]["sequence"] if items else after)}

    def send_chat(
        self,
        user_id: str,
        channel_type: str,
        channel_id: str,
        text: str,
        client_message_id: str,
    ) -> dict:
        normalized = " ".join(text.strip().split())
        if not normalized or len(normalized) > 256:
            raise bad_request("invalid_message", "A mensagem deve ter entre 1 e 256 caracteres.")
        if not client_message_id or len(client_message_id) > 96:
            raise bad_request("invalid_client_message_id", "Identificador da mensagem inválido.")
        with self.store.transaction(immediate=True) as db:
            members = self._channel_members(db, user_id, channel_type, channel_id)
            previous = db.execute(
                "SELECT * FROM chat_messages WHERE author_id=? AND client_message_id=?",
                (user_id, client_message_id),
            ).fetchone()
            if previous is not None:
                return self._chat_payload(db, previous)
            message_id = new_id("msg")
            now = self.clock()
            db.execute(
                "INSERT INTO chat_messages(message_id,channel_type,channel_id,author_id,client_message_id,text,created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (message_id, channel_type, channel_id, user_id, client_message_id, normalized, now),
            )
            row = db.execute("SELECT * FROM chat_messages WHERE message_id=?", (message_id,)).fetchone()
            payload = self._chat_payload(db, row)
            self.store.emit(db, members, "chat.message", channel_id, None, payload)
            return payload

    def chat_history(self, user_id: str, channel_type: str, channel_id: str, after: int, limit: int) -> dict:
        db = self.store.connection()
        self._channel_members(db, user_id, channel_type, channel_id)
        safe_limit = min(max(limit, 1), 100)
        rows = db.execute(
            "SELECT * FROM chat_messages WHERE channel_type=? AND channel_id=? AND sequence>? "
            "ORDER BY sequence LIMIT ?",
            (channel_type, channel_id, max(0, after), safe_limit),
        ).fetchall()
        items = [self._chat_payload(db, row) for row in rows]
        return {"items": items, "next_cursor": str(items[-1]["sequence"] if items else max(0, after))}

    def _channel_members(self, db: sqlite3.Connection, user_id: str, channel_type: str, channel_id: str) -> list[str]:
        if channel_type == "party":
            table, key = "party_members", "party_id"
        elif channel_type == "lobby":
            table, key = "lobby_members", "lobby_id"
        else:
            raise bad_request("invalid_channel", "Canal de chat inválido.")
        rows = db.execute(f"SELECT user_id FROM {table} WHERE {key}=?", (channel_id,)).fetchall()
        members = [row["user_id"] for row in rows]
        if user_id not in members:
            raise not_found()
        return members

    @staticmethod
    def _chat_payload(db: sqlite3.Connection, row: sqlite3.Row) -> dict:
        author = db.execute("SELECT display_name FROM users WHERE user_id=?", (row["author_id"],)).fetchone()
        return {
            "sequence": row["sequence"],
            "message_id": row["message_id"],
            "channel_type": row["channel_type"],
            "channel_id": row["channel_id"],
            "author_id": row["author_id"],
            "author_name": author["display_name"],
            "client_message_id": row["client_message_id"],
            "text": row["text"],
            "created_at": row["created_at"],
        }

    def issue_event_ticket(self, user_id: str) -> dict:
        ticket = new_secret()
        expires = self.clock() + 15
        with self.store.transaction(immediate=True) as db:
            db.execute(
                "INSERT INTO event_tickets(ticket_hash,user_id,expires_at) VALUES(?,?,?)",
                (token_hash(ticket), user_id, expires),
            )
        return {"ticket": ticket, "expires_at": expires, "protocol_version": 1}

    def redeem_event_ticket(self, ticket: str) -> str:
        now = self.clock()
        with self.store.transaction(immediate=True) as db:
            row = db.execute("SELECT * FROM event_tickets WHERE ticket_hash=?", (token_hash(ticket),)).fetchone()
            if row is None or row["expires_at"] <= now or row["used_at"] is not None:
                raise ServiceError(401, "invalid_ticket", "O ticket de eventos é inválido.")
            db.execute("UPDATE event_tickets SET used_at=? WHERE ticket_hash=?", (now, token_hash(ticket)))
            return row["user_id"]

    def _require_user(self, db: sqlite3.Connection, user_id: str) -> sqlite3.Row:
        row = db.execute("SELECT * FROM users WHERE user_id=? AND status='active'", (user_id,)).fetchone()
        if row is None:
            raise not_found()
        return row

    def _require_account(self, db: sqlite3.Connection, user_id: str) -> sqlite3.Row:
        row = self._require_user(db, user_id)
        if row["user_type"] == "guest":
            raise forbidden("guest_restricted", "Converta o convidado em conta para usar amizades.")
        return row

    def _is_blocked(self, db: sqlite3.Connection, first: str, second: str) -> bool:
        return bool(
            db.execute(
                "SELECT 1 FROM blocks WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)",
                (first, second, second, first),
            ).fetchone()
        )

    def _friend_ids(self, db: sqlite3.Connection, user_id: str) -> list[str]:
        return [
            row[0]
            for row in db.execute(
                "SELECT CASE WHEN user_low=? THEN user_high ELSE user_low END FROM friendships WHERE user_low=? OR user_high=?",
                (user_id, user_id, user_id),
            )
        ]
