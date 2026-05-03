from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .transport import DatagramEndpoint


@dataclass(frozen=True)
class DiscoveredServer:
    announcement: object
    address: tuple[str, int]
    last_seen: float


class DiscoveryService:
    DEFAULT_INTERVAL_SECONDS = 1.0

    def __init__(self, *, encode: Callable[[object], bytes], decode: Callable[[bytes], object]):
        self._encode = encode
        self._decode = decode

    def encode_announcement(self, announcement: object) -> bytes:
        return self._encode(announcement)

    def decode_announcement(self, payload: bytes) -> object:
        return self._decode(payload)

    def open_broadcast_endpoint(self, *, host: str = "", port: int = 0) -> DatagramEndpoint:
        return DatagramEndpoint(host=host, port=port, broadcast=True, reuse_address=True)

    def open_listen_endpoint(self, *, host: str = "", port: int) -> DatagramEndpoint:
        return DatagramEndpoint(host=host, port=port, reuse_address=True)

    def broadcast(
        self,
        endpoint: DatagramEndpoint,
        announcement: object,
        *,
        host: str = "255.255.255.255",
        port: int,
    ):
        endpoint.sendto(self.encode_announcement(announcement), (host, port))


class ServerBrowser:
    def __init__(
        self,
        *,
        expiry_seconds: float = 3.0,
        expected_protocol_version: int = 1,
        protocol_getter: Callable[[object], int] | None = None,
        key_factory: Callable[[object, tuple[str, int]], tuple[object, ...]] | None = None,
    ):
        self._expiry_seconds = expiry_seconds
        self._expected_protocol_version = expected_protocol_version
        self._protocol_getter = protocol_getter or (
            lambda announcement: int(getattr(announcement, "protocol_version", 0))
        )
        self._key_factory = key_factory or (
            lambda announcement, address: (
                address[0],
                int(getattr(announcement, "server_port", address[1])),
                str(getattr(announcement, "session_id", "")),
            )
        )
        self._servers_by_key: dict[tuple[object, ...], DiscoveredServer] = {}

    def record_announcement(
        self,
        announcement: object,
        address: tuple[str, int],
        *,
        now: float,
    ) -> bool:
        if self._protocol_getter(announcement) != self._expected_protocol_version:
            return False
        key = self._key_factory(announcement, address)
        self._servers_by_key[key] = DiscoveredServer(announcement=announcement, address=address, last_seen=now)
        return True

    def get_servers(self, *, now: float) -> tuple[DiscoveredServer, ...]:
        expired = [
            key
            for key, entry in self._servers_by_key.items()
            if (now - entry.last_seen) > self._expiry_seconds
        ]
        for key in expired:
            self._servers_by_key.pop(key, None)
        return tuple(
            sorted(
                self._servers_by_key.values(),
                key=lambda entry: (str(getattr(entry.announcement, "server_name", "")), entry.address),
            )
        )
