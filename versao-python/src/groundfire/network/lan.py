from __future__ import annotations

import socket
from dataclasses import dataclass

from groundfire_net.discovery import DiscoveryService, ServerBrowser

from ..sim.match import MatchState
from .codec import decode_message, encode_message
from .messages import DEFAULT_DISCOVERY_PORT, PROTOCOL_VERSION, LanServerAnnouncement


@dataclass(frozen=True)
class DiscoveredLanServer:
    announcement: LanServerAnnouncement
    address: tuple[str, int]
    last_seen: float


class LanDiscoveryService:
    DEFAULT_INTERVAL_SECONDS = 1.0

    def __init__(self, *, interval_seconds: float = DEFAULT_INTERVAL_SECONDS):
        self._interval_seconds = interval_seconds
        self._service = DiscoveryService(encode=encode_message, decode=decode_message)

    def build_announcement(
        self,
        match_state: MatchState,
        *,
        server_name: str,
        map_seed: int,
        max_players: int,
        requires_password: bool,
        server_port: int,
        region: str = "world",
        secure: bool = True,
    ) -> LanServerAnnouncement:
        return LanServerAnnouncement(
            server_name=server_name,
            session_id=match_state.session_id,
            map_seed=map_seed,
            current_round=match_state.current_round,
            player_count=len(match_state.player_slots),
            max_players=max_players,
            requires_password=requires_password,
            server_port=server_port,
            region=region,
            secure=secure,
        )

    def encode_announcement(self, announcement: LanServerAnnouncement) -> bytes:
        return self._service.encode_announcement(announcement)

    def decode_announcement(self, payload: bytes) -> LanServerAnnouncement:
        message = self._service.decode_announcement(payload)
        if not isinstance(message, LanServerAnnouncement):
            raise ValueError(f"Expected LanServerAnnouncement, got {type(message)!r}")
        return message

    def open_broadcast_socket(self, *, host: str = "", port: int = 0):
        return self._service.open_broadcast_endpoint(host=host, port=port).socket

    def broadcast(
        self,
        sock: socket.socket,
        announcement: LanServerAnnouncement,
        *,
        host: str = "255.255.255.255",
        port: int = DEFAULT_DISCOVERY_PORT,
    ):
        sock.sendto(self.encode_announcement(announcement), (host, port))


class LanServerBrowser:
    def __init__(
        self,
        *,
        expiry_seconds: float = 3.0,
        expected_protocol_version: int = PROTOCOL_VERSION,
    ):
        self._expiry_seconds = expiry_seconds
        self._expected_protocol_version = expected_protocol_version
        self._browser = ServerBrowser(
            expiry_seconds=expiry_seconds,
            expected_protocol_version=expected_protocol_version,
        )
        self._servers_by_key: dict[tuple[str, int, str], DiscoveredLanServer] = {}

    def record_announcement(
        self,
        announcement: LanServerAnnouncement,
        address: tuple[str, int],
        *,
        now: float,
    ) -> bool:
        recorded = self._browser.record_announcement(announcement, address, now=now)
        if not recorded:
            return False

        key = (address[0], int(announcement.server_port), announcement.session_id)
        self._servers_by_key[key] = DiscoveredLanServer(announcement=announcement, address=address, last_seen=now)
        return True

    def get_servers(self, *, now: float) -> tuple[DiscoveredLanServer, ...]:
        self._browser.get_servers(now=now)
        expired = []
        for key, entry in self._servers_by_key.items():
            if (now - entry.last_seen) > self._expiry_seconds:
                expired.append(key)

        for key in expired:
            self._servers_by_key.pop(key, None)

        return tuple(
            sorted(
                self._servers_by_key.values(),
                key=lambda entry: (entry.announcement.server_name, entry.address),
            )
        )
