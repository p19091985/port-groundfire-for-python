from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from time import perf_counter
from typing import Dict, List, Optional, Sequence, Tuple

from .lan_protocol import LAN_DISCOVERY_PORT, LanLobbySnapshot, LanPlayerDescriptor

@dataclass(frozen=True)
class LanConnectionResult:
    status: str
    server_name: str
    map_name: str
    network: str
    host: str
    port: int
    max_players: int
    current_players: int
    secure: bool
    client_name: str
    player_id: str
    slot_index: int
    players: Tuple[str, ...]
    player_slots: Tuple[LanPlayerDescriptor, ...]
    rounds: int
    lobby_state: str
    countdown_seconds: int
    match_started: bool
    match_id: str
    landscape_seed: int
    tank_seed: int


@dataclass(frozen=True)
class LanFrameSyncResult:
    status: str
    slot_index: int
    commands_by_slot: Dict[int, Tuple[bool, ...]]
    current_round: int


@dataclass(frozen=True)
class LanDiscoveredServer:
    snapshot: LanLobbySnapshot
    latency_ms: int

    @property
    def server_id(self) -> str:
        return f"{self.snapshot.host}:{self.snapshot.port}"


class LanClient:
    def discover_lan(
        self,
        timeout: float = 0.35,
        discovery_port: int = LAN_DISCOVERY_PORT,
        targets: Optional[Sequence[str]] = None,
    ) -> List[LanDiscoveredServer]:
        targets = tuple(targets or ("127.0.0.1", "255.255.255.255"))
        request = {
            "action": "discover",
            "network": "Lan",
        }

        discovered: Dict[Tuple[str, int], LanDiscoveredServer] = {}
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(timeout)
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            payload = json.dumps(request).encode("utf-8")
            for target in targets:
                try:
                    connection.sendto(payload, (target, discovery_port))
                except OSError:
                    continue

            started_at = perf_counter()
            while True:
                try:
                    response, _address = connection.recvfrom(4096)
                except socket.timeout:
                    break
                except OSError:
                    break

                latency_ms = max(1, int((perf_counter() - started_at) * 1000))
                try:
                    payload_dict = json.loads(response.decode("utf-8").splitlines()[0])
                except (IndexError, json.JSONDecodeError):
                    continue
                if payload_dict.get("status") != "ok":
                    continue

                snapshot = LanLobbySnapshot.from_payload(payload_dict)
                key = (snapshot.host, snapshot.port)
                discovered[key] = LanDiscoveredServer(snapshot=snapshot, latency_ms=latency_ms)

        return sorted(discovered.values(), key=lambda item: (item.snapshot.server_name.lower(), item.snapshot.port))

    def connect(
        self,
        host: str,
        port: int,
        client_name: str = "LAN Client",
        use_ai: bool = False,
        timeout: float = 2.0,
    ) -> LanConnectionResult:
        request = {
            "action": "join",
            "client_name": client_name,
            "use_ai": use_ai,
        }

        payload = self._request(host, port, request, timeout)
        return self._result_from_payload(payload, client_name)

    def get_lobby_status(
        self,
        host: str,
        port: int,
        player_id: str,
        timeout: float = 2.0,
    ) -> LanConnectionResult:
        payload = self._request(host, port, {"action": "status", "player_id": player_id}, timeout)
        return self._result_from_payload(payload, "")

    def leave(
        self,
        host: str,
        port: int,
        player_id: str,
        timeout: float = 2.0,
    ) -> None:
        self._request(host, port, {"action": "leave", "player_id": player_id}, timeout)

    def sync_frame(
        self,
        host: str,
        port: int,
        player_id: str,
        frame_index: int,
        commands: Sequence[bool],
        current_round: int,
        timeout: float = 0.2,
    ) -> LanFrameSyncResult:
        payload = self._request(
            host,
            port,
            {
                "action": "frame",
                "player_id": player_id,
                "frame_index": int(frame_index),
                "commands": [bool(command) for command in commands],
                "current_round": int(current_round),
            },
            timeout,
        )
        commands_by_slot = {
            int(slot_index): tuple(bool(command) for command in slot_commands)
            for slot_index, slot_commands in payload.get("commands_by_slot", {}).items()
        }
        return LanFrameSyncResult(
            status=str(payload.get("status", "error")),
            slot_index=int(payload.get("slot_index", -1)),
            commands_by_slot=commands_by_slot,
            current_round=int(payload.get("current_round", current_round)),
        )

    def _request(self, host: str, port: int, request: Dict[str, object], timeout: float) -> Dict[str, object]:
        with socket.create_connection((host, port), timeout=timeout) as connection:
            connection.settimeout(timeout)
            connection.sendall((json.dumps(request) + "\n").encode("utf-8"))
            response = self._recv_line(connection)
        return json.loads(response)

    @staticmethod
    def _result_from_payload(payload: Dict[str, object], default_client_name: str) -> LanConnectionResult:
        snapshot = LanLobbySnapshot.from_payload(payload)
        return LanConnectionResult(
            status=str(payload["status"]),
            server_name=snapshot.server_name,
            map_name=snapshot.map_name,
            network=snapshot.network,
            host=snapshot.host,
            port=snapshot.port,
            max_players=snapshot.max_players,
            current_players=snapshot.current_players,
            secure=snapshot.secure,
            client_name=str(payload.get("client_name", default_client_name)),
            player_id=str(payload.get("player_id", "")),
            slot_index=int(payload.get("slot_index", -1)),
            players=snapshot.players,
            player_slots=snapshot.player_slots,
            rounds=snapshot.rounds,
            lobby_state=snapshot.lobby_state,
            countdown_seconds=snapshot.countdown_seconds,
            match_started=snapshot.match_started,
            match_id=snapshot.match_id,
            landscape_seed=snapshot.landscape_seed,
            tank_seed=snapshot.tank_seed,
        )

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
            raise ConnectionError("No response received from LAN server.")
        return payload[0]
