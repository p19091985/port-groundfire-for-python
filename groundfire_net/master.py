from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass

from .browser import ServerListEntry
from .transport import DatagramEndpoint

DEFAULT_MASTER_PORT = 27017
MASTER_PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class MasterServerAddress:
    host: str
    port: int = DEFAULT_MASTER_PORT


@dataclass(frozen=True)
class MasterQuery:
    game: str = "Groundfire"
    region: str = ""
    secure_only: bool = False
    include_passworded: bool = True
    include_full: bool = True
    include_empty: bool = True
    protocol_version: int = MASTER_PROTOCOL_VERSION


class MasterServerDirectory:
    def __init__(self, *, ttl_seconds: float = 90.0, now=None):
        self._ttl_seconds = ttl_seconds
        self._now = now or time.monotonic
        self._entries: dict[str, tuple[ServerListEntry, float]] = {}

    def register(self, entry: ServerListEntry, *, source_host: str) -> ServerListEntry:
        host = entry.host.strip()
        if not host or host in {"0.0.0.0", "::"}:
            host = source_host
        registered = entry.with_updates(host=host, source="internet")
        self._entries[registered.endpoint] = (registered, self._now())
        return registered

    def unregister(self, host: str, port: int):
        self._entries.pop(f"{host}:{port}", None)

    def query(self, query: MasterQuery | None = None) -> tuple[ServerListEntry, ...]:
        self.prune()
        query = query or MasterQuery()
        entries = tuple(entry for entry, _last_seen in self._entries.values())
        return tuple(entry for entry in entries if self._matches(entry, query))

    def prune(self):
        now = self._now()
        expired = [
            endpoint
            for endpoint, (_entry, last_seen) in self._entries.items()
            if (now - last_seen) > self._ttl_seconds
        ]
        for endpoint in expired:
            self._entries.pop(endpoint, None)

    def _matches(self, entry: ServerListEntry, query: MasterQuery) -> bool:
        if query.game and entry.game.lower() != query.game.lower():
            return False
        if query.region and entry.region.lower() != query.region.lower():
            return False
        if query.secure_only and not entry.secure:
            return False
        if not query.include_passworded and entry.requires_password:
            return False
        if not query.include_full and entry.player_count >= entry.max_players:
            return False
        if not query.include_empty and entry.player_count <= 0:
            return False
        return True


class MasterServerApp:
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = DEFAULT_MASTER_PORT,
        directory: MasterServerDirectory | None = None,
    ):
        self._host = host
        self._port = port
        self._directory = directory or MasterServerDirectory()
        self._endpoint: DatagramEndpoint | None = None

    def open(self):
        if self._endpoint is None:
            self._endpoint = DatagramEndpoint(host=self._host, port=self._port, reuse_address=True)
        return self

    def close(self):
        if self._endpoint is not None:
            self._endpoint.close()
            self._endpoint = None

    def get_bound_port(self) -> int:
        if self._endpoint is None:
            return self._port
        return self._endpoint.get_bound_port()

    def poll(self, *, timeout: float = 0.0) -> tuple[object, ...]:
        self.open()
        assert self._endpoint is not None
        responses = []
        for datagram in self._endpoint.poll(timeout=timeout):
            try:
                message_type, payload = decode_master_packet(datagram.payload)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
            if message_type == "register":
                entry = _entry_from_payload(payload)
                registered = self._directory.register(entry, source_host=datagram.address[0])
                response = ("register_ok", {"entry": asdict(registered)})
            elif message_type == "unregister":
                self._directory.unregister(str(payload.get("host", "")), int(payload.get("port", 0)))
                response = ("unregister_ok", {})
            elif message_type == "query":
                entries = self._directory.query(_query_from_payload(payload))
                response = ("query_response", {"entries": [asdict(entry) for entry in entries]})
            else:
                continue
            self._endpoint.sendto(encode_master_packet(*response), datagram.address)
            responses.append(response)
        self._directory.prune()
        return tuple(responses)


class MasterServerClient:
    def __init__(self):
        self._endpoint: DatagramEndpoint | None = None

    def close(self):
        if self._endpoint is not None:
            self._endpoint.close()
            self._endpoint = None

    def register(
        self,
        address: MasterServerAddress,
        entry: ServerListEntry,
        *,
        timeout: float = 0.05,
    ) -> ServerListEntry | None:
        response = self._request(address, "register", asdict(entry), timeout=timeout)
        if response is None:
            return None
        message_type, payload = response
        if message_type != "register_ok":
            return None
        return _entry_from_payload(payload.get("entry", {}))

    def unregister(self, address: MasterServerAddress, *, host: str, port: int, timeout: float = 0.02) -> bool:
        response = self._request(address, "unregister", {"host": host, "port": port}, timeout=timeout)
        return response is not None and response[0] == "unregister_ok"

    def query(
        self,
        address: MasterServerAddress,
        query: MasterQuery | None = None,
        *,
        timeout: float = 0.05,
    ) -> tuple[ServerListEntry, ...]:
        response = self._request(address, "query", asdict(query or MasterQuery()), timeout=timeout)
        if response is None or response[0] != "query_response":
            return ()
        return tuple(_entry_from_payload(raw) for raw in response[1].get("entries", ()))

    def _request(
        self,
        address: MasterServerAddress,
        message_type: str,
        payload: dict,
        *,
        timeout: float,
    ) -> tuple[str, dict] | None:
        endpoint = self._ensure_endpoint()
        endpoint.sendto(encode_master_packet(message_type, payload), (address.host, address.port))
        deadline = time.monotonic() + timeout
        while time.monotonic() <= deadline:
            for datagram in endpoint.poll(timeout=0.002):
                try:
                    return decode_master_packet(datagram.payload)
                except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                    continue
        return None

    def _ensure_endpoint(self) -> DatagramEndpoint:
        if self._endpoint is None:
            self._endpoint = DatagramEndpoint(host="", port=0)
        return self._endpoint


def encode_master_packet(message_type: str, payload: dict) -> bytes:
    return json.dumps(
        {
            "message_type": message_type,
            "payload": payload,
            "protocol_version": MASTER_PROTOCOL_VERSION,
        },
        sort_keys=True,
    ).encode("utf-8")


def decode_master_packet(packet: bytes) -> tuple[str, dict]:
    decoded = json.loads(packet.decode("utf-8"))
    return str(decoded["message_type"]), dict(decoded.get("payload", {}))


def parse_master_server_address(raw: str) -> MasterServerAddress:
    value = raw.strip()
    if not value:
        return MasterServerAddress("127.0.0.1", DEFAULT_MASTER_PORT)
    if ":" not in value:
        return MasterServerAddress(value, DEFAULT_MASTER_PORT)
    host, raw_port = value.rsplit(":", 1)
    return MasterServerAddress(host.strip() or "127.0.0.1", int(raw_port))


def _entry_from_payload(payload: dict) -> ServerListEntry:
    return ServerListEntry(
        name=str(payload.get("name", "Groundfire Server")),
        host=str(payload.get("host", "")),
        port=int(payload.get("port", 0)),
        game=str(payload.get("game", "Groundfire")),
        map_name=str(payload.get("map_name", "generated")),
        player_count=int(payload.get("player_count", 0)),
        max_players=int(payload.get("max_players", 8)),
        latency_ms=None if payload.get("latency_ms") is None else int(payload.get("latency_ms")),
        source=str(payload.get("source", "internet")),
        description=str(payload.get("description", "")),
        last_played=str(payload.get("last_played", "")),
        requires_password=bool(payload.get("requires_password", False)),
        region=str(payload.get("region", "world")),
        secure=bool(payload.get("secure", True)),
        protocol_version=int(payload.get("protocol_version", MASTER_PROTOCOL_VERSION)),
    )


def _query_from_payload(payload: dict) -> MasterQuery:
    return MasterQuery(
        game=str(payload.get("game", "Groundfire")),
        region=str(payload.get("region", "")),
        secure_only=bool(payload.get("secure_only", False)),
        include_passworded=bool(payload.get("include_passworded", True)),
        include_full=bool(payload.get("include_full", True)),
        include_empty=bool(payload.get("include_empty", True)),
        protocol_version=int(payload.get("protocol_version", MASTER_PROTOCOL_VERSION)),
    )
