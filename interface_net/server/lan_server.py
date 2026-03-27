from __future__ import annotations

import json
import socket
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ..lan_protocol import LAN_DISCOVERY_PORT, LanLobbySnapshot, LanPlayerDescriptor


@dataclass(frozen=True)
class LanServerInfo:
    server_name: str
    map_name: str
    network: str
    host: str
    port: int
    max_players: int
    current_players: int
    secure: bool
    rounds: int
    lobby_state: str
    countdown_seconds: int
    match_started: bool


class DedicatedLanServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 0,
        server_name: str = "Groundfire LAN",
        map_name: str = "Canyon",
        max_players: int = 12,
        secure: bool = True,
        rounds: int = 10,
        network: str = "Lan",
        discovery_port: int = LAN_DISCOVERY_PORT,
        countdown_seconds: float = 30.0,
        player_timeout: float = 10.0,
        time_provider: Optional[Callable[[], float]] = None,
        advertise_host: Optional[str] = None,
        log_path: str = "logs/dedicated_server.log",
        log_callback: Optional[Callable[[str], None]] = None,
    ):
        self._host = host
        self._port = port
        self._advertise_host = advertise_host
        self._server_name = server_name
        self._map_name = map_name
        self._max_players = max_players
        self._secure = secure
        self._rounds = rounds
        self._network = network
        self._discovery_port = discovery_port
        self._countdown_seconds = countdown_seconds
        self._player_timeout = player_timeout
        self._time_provider = time_provider or time.monotonic
        self._log_path = Path(log_path)
        self._log_callback = log_callback
        self._log_lock = threading.Lock()
        self._socket: Optional[socket.socket] = None
        self._discovery_socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._discovery_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._connected_clients: Dict[str, Dict[str, object]] = {}
        self._countdown_deadline: Optional[float] = None
        self._match_started = False
        self._match_id = ""
        self._landscape_seed = 0
        self._tank_seed = 0

    def start(self) -> None:
        if self._running:
            return

        self._log_event(
            f"Starting server '{self._server_name}' on requested port {self._port or 0} "
            f"for map '{self._map_name}' with {self._max_players} slots and {self._rounds} rounds."
        )
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen()
        self._socket.settimeout(0.2)
        bound_host, bound_port = self._socket.getsockname()
        self._host = bound_host
        self._port = bound_port
        if not self._advertise_host:
            self._advertise_host = self._resolve_advertise_host(bound_host)
        self._log_event(
            f"Server online at {self._advertise_host or self._host}:{self._port} "
            f"(network={self._network}, secure={self._secure})."
        )

        if self._network.lower() == "lan":
            self._discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._discovery_socket.bind(("", self._discovery_port))
            self._discovery_socket.settimeout(0.2)
            self._log_event(f"LAN discovery responder listening on UDP {self._discovery_port}.")

        self._running = True
        self._thread = threading.Thread(target=self._serve_forever, daemon=True)
        self._thread.start()
        if self._discovery_socket is not None:
            self._discovery_thread = threading.Thread(target=self._serve_discovery, daemon=True)
            self._discovery_thread.start()

    def stop(self) -> None:
        should_log_stop = self._running or self._socket is not None or self._discovery_socket is not None
        self._running = False
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        if self._discovery_socket is not None:
            try:
                self._discovery_socket.close()
            except OSError:
                pass
            self._discovery_socket = None

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        if self._discovery_thread is not None:
            self._discovery_thread.join(timeout=1.0)
            self._discovery_thread = None

        if should_log_stop:
            self._log_event("Dedicated server stopped.")

    def get_server_info(self) -> LanServerInfo:
        snapshot = self.get_lobby_snapshot()

        return LanServerInfo(
            server_name=snapshot.server_name,
            map_name=snapshot.map_name,
            network=snapshot.network,
            host=snapshot.host,
            port=snapshot.port,
            max_players=snapshot.max_players,
            current_players=snapshot.current_players,
            secure=snapshot.secure,
            rounds=snapshot.rounds,
            lobby_state=snapshot.lobby_state,
            countdown_seconds=snapshot.countdown_seconds,
            match_started=snapshot.match_started,
        )

    def get_log_path(self) -> str:
        return str(self._log_path)

    def get_connected_clients(self) -> List[str]:
        with self._lock:
            self._update_lobby_state_locked(self._time_provider())
            ordered_clients = sorted(
                self._connected_clients.values(),
                key=lambda client: int(client["slot_index"]),
            )
            return [str(client["name"]) for client in ordered_clients]

    def get_lobby_snapshot(self) -> LanLobbySnapshot:
        with self._lock:
            return self._get_snapshot_locked(self._time_provider())

    def _serve_forever(self) -> None:
        while self._running:
            try:
                assert self._socket is not None
                connection, _address = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with connection:
                connection.settimeout(1.0)
                try:
                    request = self._recv_line(connection)
                    payload = json.loads(request)
                    response = self._handle_request(payload, _address)
                    connection.sendall((json.dumps(response) + "\n").encode("utf-8"))
                except (ConnectionError, json.JSONDecodeError, OSError) as exc:
                    self._log_event(
                        f"Failed to handle request from {self._format_remote_address(_address)}: {exc}",
                        level="WARN",
                    )
                    continue

    def _serve_discovery(self) -> None:
        while self._running:
            try:
                assert self._discovery_socket is not None
                data, address = self._discovery_socket.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                payload = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            if payload.get("action") != "discover":
                continue
            if payload.get("network", "Lan").lower() != self._network.lower():
                continue

            snapshot = self.get_lobby_snapshot()
            response = {"status": "ok", "type": "discovery", **snapshot.to_payload()}
            try:
                self._discovery_socket.sendto((json.dumps(response) + "\n").encode("utf-8"), address)
            except OSError:
                continue

    def _handle_request(self, payload: Dict[str, object], remote_address=None) -> Dict[str, object]:
        action = str(payload.get("action", "")).lower()
        now = self._time_provider()
        remote_label = self._format_remote_address(remote_address)
        with self._lock:
            if action == "join":
                client_name = str(payload.get("client_name", "LAN Client")).strip() or "LAN Client"
                use_ai = bool(payload.get("use_ai", False))
                self._update_lobby_state_locked(now)
                if self._match_started:
                    snapshot = self._get_snapshot_locked(now)
                    self._log_event(
                        f"Rejected join from {remote_label} for '{client_name}': match already started.",
                        level="WARN",
                    )
                    return {"status": "error", "reason": "match_already_started", **snapshot.to_payload()}
                if len(self._connected_clients) >= self._max_players:
                    snapshot = self._get_snapshot_locked(now)
                    self._log_event(
                        f"Rejected join from {remote_label} for '{client_name}': server is full.",
                        level="WARN",
                    )
                    return {"status": "error", "reason": "server_full", **snapshot.to_payload()}

                player_id = uuid.uuid4().hex
                slot_index = self._next_available_slot_locked()
                self._connected_clients[player_id] = {
                    "name": client_name,
                    "joined_at": now,
                    "last_seen": now,
                    "slot_index": slot_index,
                    "use_ai": use_ai,
                    "commands": tuple(False for _ in range(11)),
                    "frame_index": -1,
                }
                self._log_event(
                    f"Player '{client_name}' joined from {remote_label} as slot {slot_index} "
                    f"(ai={'on' if use_ai else 'off'})."
                )
                snapshot = self._get_snapshot_locked(now)
                return {
                    "status": "ok",
                    "player_id": player_id,
                    "slot_index": slot_index,
                    "client_name": client_name,
                    **snapshot.to_payload(),
                }

            if action == "status":
                player_id = str(payload.get("player_id", ""))
                if player_id in self._connected_clients:
                    self._connected_clients[player_id]["last_seen"] = now
                snapshot = self._get_snapshot_locked(now)
                if player_id not in self._connected_clients and not snapshot.match_started:
                    return {"status": "error", "reason": "unknown_player", **snapshot.to_payload()}
                slot_index = int(self._connected_clients.get(player_id, {}).get("slot_index", -1))
                return {"status": "ok", "player_id": player_id, "slot_index": slot_index, **snapshot.to_payload()}

            if action == "frame":
                player_id = str(payload.get("player_id", ""))
                client = self._connected_clients.get(player_id)
                snapshot = self._get_snapshot_locked(now)
                if client is None:
                    return {"status": "error", "reason": "unknown_player", **snapshot.to_payload()}

                client["last_seen"] = now
                commands = tuple(bool(command) for command in payload.get("commands", []))
                if len(commands) < 11:
                    commands = commands + tuple(False for _ in range(11 - len(commands)))
                client["commands"] = commands[:11]
                client["frame_index"] = int(payload.get("frame_index", -1))

                commands_by_slot = {
                    str(int(remote_client["slot_index"])): list(remote_client.get("commands", tuple(False for _ in range(11))))
                    for remote_client in sorted(
                        self._connected_clients.values(),
                        key=lambda remote_client: int(remote_client["slot_index"]),
                    )
                }
                return {
                    "status": "ok",
                    "player_id": player_id,
                    "slot_index": int(client["slot_index"]),
                    "current_round": int(payload.get("current_round", 1)),
                    "commands_by_slot": commands_by_slot,
                    **snapshot.to_payload(),
                }

            if action == "leave":
                player_id = str(payload.get("player_id", ""))
                client = self._connected_clients.pop(player_id, None)
                if client is not None:
                    self._log_event(
                        f"Player '{client['name']}' left the server from slot {client['slot_index']}."
                    )
                snapshot = self._get_snapshot_locked(now)
                return {"status": "ok", "player_id": player_id, **snapshot.to_payload()}

            snapshot = self._get_snapshot_locked(now)
            self._log_event(
                f"Received unknown action '{action or 'empty'}' from {remote_label}.",
                level="WARN",
            )
            return {"status": "error", "reason": "unknown_action", **snapshot.to_payload()}

    def _get_snapshot_locked(self, now: float) -> LanLobbySnapshot:
        self._update_lobby_state_locked(now)
        ordered_clients = sorted(
            self._connected_clients.values(),
            key=lambda client: int(client["slot_index"]),
        )
        player_slots = tuple(
            LanPlayerDescriptor(
                slot_index=int(player["slot_index"]),
                name=str(player["name"]),
                uses_ai=bool(player.get("use_ai", False)),
            )
            for player in ordered_clients
        )
        player_names = tuple(player.name for player in player_slots)
        countdown_seconds = 0
        if self._countdown_deadline is not None and not self._match_started:
            countdown_seconds = max(0, int(self._countdown_deadline - now + 0.999))

        lobby_state = "started" if self._match_started else ("countdown" if self._countdown_deadline is not None else "waiting")
        return LanLobbySnapshot(
            server_name=self._server_name,
            map_name=self._map_name,
            network=self._network,
            host=self._advertise_host or self._host,
            port=self._port,
            max_players=self._max_players,
            current_players=len(self._connected_clients),
            secure=self._secure,
            players=player_names,
            player_slots=player_slots,
            rounds=self._rounds,
            lobby_state=lobby_state,
            countdown_seconds=countdown_seconds,
            match_started=self._match_started,
            match_id=self._match_id,
            landscape_seed=self._landscape_seed,
            tank_seed=self._tank_seed,
        )

    def _update_lobby_state_locked(self, now: float) -> None:
        expired_players = [
            player_id
            for player_id, player in self._connected_clients.items()
            if (now - float(player["last_seen"])) > self._player_timeout
        ]
        for player_id in expired_players:
            client = self._connected_clients.pop(player_id, None)
            if client is not None:
                self._log_event(
                    f"Player '{client['name']}' timed out and was removed from slot {client['slot_index']}.",
                    level="WARN",
                )

        player_count = len(self._connected_clients)

        if self._match_started:
            return

        if player_count < 2:
            if self._countdown_deadline is not None:
                self._log_event("Match countdown reset because fewer than 2 players remain connected.")
            self._countdown_deadline = None
            self._match_id = ""
            self._landscape_seed = 0
            self._tank_seed = 0
            return

        if self._countdown_deadline is None:
            self._countdown_deadline = now + self._countdown_seconds
            self._log_event(
                f"Match countdown started for {self._countdown_seconds:.1f}s with {player_count} connected players."
            )
            return

        if now >= self._countdown_deadline:
            self._match_started = True
            self._create_match_locked()

    def _create_match_locked(self) -> None:
        if self._match_id:
            return
        seed_material = uuid.uuid4().hex
        self._match_id = seed_material
        self._landscape_seed = int(seed_material[:8], 16)
        self._tank_seed = int(seed_material[8:16], 16)
        player_names = ", ".join(
            str(client["name"])
            for client in sorted(self._connected_clients.values(), key=lambda client: int(client["slot_index"]))
        ) or "-"
        self._log_event(
            f"Match {self._match_id} started with players [{player_names}], rounds={self._rounds}, "
            f"landscape_seed={self._landscape_seed}, tank_seed={self._tank_seed}."
        )

    def _next_available_slot_locked(self) -> int:
        used_slots = {int(client["slot_index"]) for client in self._connected_clients.values()}
        slot_index = 0
        while slot_index in used_slots:
            slot_index += 1
        return slot_index

    @staticmethod
    def _resolve_advertise_host(bound_host: str) -> str:
        if bound_host and bound_host not in ("0.0.0.0", "::"):
            return bound_host

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.connect(("10.255.255.255", 1))
                return str(probe.getsockname()[0])
        except OSError:
            return "127.0.0.1"

    @staticmethod
    def _recv_line(connection: socket.socket) -> str:
        chunks = []
        while True:
            chunk = connection.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break

        payload = b"".join(chunks).decode("utf-8").splitlines()
        if not payload:
            raise ConnectionError("No request received by LAN server.")
        return payload[0]

    @staticmethod
    def _format_remote_address(address) -> str:
        if not address:
            return "unknown"
        host = str(address[0]) if len(address) > 0 else "unknown"
        port = str(address[1]) if len(address) > 1 else "?"
        return f"{host}:{port}"

    def _log_event(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"

        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_lock:
                with self._log_path.open("a", encoding="utf-8") as handle:
                    handle.write(entry + "\n")
        except OSError:
            pass

        if self._log_callback is not None:
            try:
                self._log_callback(entry)
            except Exception:
                pass
