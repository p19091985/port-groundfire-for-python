from __future__ import annotations

import os
import uuid
from pathlib import Path

from groundfire_net.browser import ServerBook, ServerListEntry
from groundfire_net.master import (
    DEFAULT_MASTER_PORT,
    MasterQuery,
    MasterServerAddress,
    MasterServerClient,
    parse_master_server_address,
)
from groundfire_net.transport import DatagramEndpoint

from ..core.headless import HeadlessRuntime
from .codec import decode_message, encode_message
from .lan import DiscoveredLanServer, LanDiscoveryService, LanServerBrowser
from .messages import DEFAULT_DISCOVERY_PORT, DEFAULT_GAME_PORT, PROTOCOL_VERSION, LanServerAnnouncement, Ping, Pong


class GroundfireServerScanner:
    """LAN scanner plus persistent favorites/history for the in-game browser."""

    def __init__(
        self,
        *,
        runtime: HeadlessRuntime | None = None,
        discovery_port: int = DEFAULT_DISCOVERY_PORT,
        server_book: ServerBook | None = None,
        master_servers: tuple[str | tuple[str, int] | MasterServerAddress, ...] | None = None,
    ):
        self._runtime = runtime or HeadlessRuntime()
        self._discovery_port = discovery_port
        self._lan = LanDiscoveryService()
        self._browser = LanServerBrowser()
        self._book = server_book or ServerBook()
        self._master_servers = _normalize_master_servers(
            tuple(default_master_server_addresses()) if master_servers is None else master_servers
        )
        self._master_client = MasterServerClient()
        self._listen_endpoint: DatagramEndpoint | None = None
        self._last_refresh_time = 0.0

    def open(self):
        if self._listen_endpoint is None:
            self._listen_endpoint = DatagramEndpoint(host="", port=self._discovery_port, reuse_address=True)
        return self

    def close(self):
        endpoint = self._listen_endpoint
        self._listen_endpoint = None
        if endpoint is not None:
            endpoint.close()
        self._master_client.close()

    def refresh(self):
        self.open()
        self._last_refresh_time = self._runtime.now()
        self.poll()

    def refresh_tab(self, tab: str, *, timeout: float = 0.02) -> tuple[ServerListEntry, ...]:
        if tab in {"internet", "unique"}:
            self.refresh_master_servers(timeout=timeout)
        self.refresh()
        entries = self.entries_for_tab(tab)
        refreshed = tuple(self.refresh_entry(entry, timeout=timeout) for entry in entries)
        for entry in refreshed:
            self._book.update_entry(entry)
        return refreshed

    def refresh_master_servers(self, *, timeout: float = 0.05) -> tuple[ServerListEntry, ...]:
        if not self._master_servers:
            return ()
        entries: list[ServerListEntry] = []
        query = MasterQuery(game="Groundfire")
        for address in self._master_servers:
            try:
                entries.extend(self._master_client.query(address, query, timeout=timeout))
            except OSError:
                continue
        unique = _unique_entries(tuple(entries))
        self._book.set_internet_servers(unique)
        return unique

    def refresh_entry(self, entry: ServerListEntry, *, timeout: float = 0.05) -> ServerListEntry:
        latency = self._ping_latency(entry.host, entry.port, timeout=timeout)
        if latency is None:
            return entry.with_updates(latency_ms=None)
        return entry.with_updates(latency_ms=latency)

    def poll(self):
        if self._listen_endpoint is None:
            return
        now = self._runtime.now()
        for datagram in self._listen_endpoint.poll(timeout=0.0):
            try:
                announcement = self._lan.decode_announcement(datagram.payload)
            except (ValueError, KeyError, TypeError):
                continue
            self._browser.record_announcement(announcement, datagram.address, now=now)

    def entries_for_tab(self, tab: str) -> tuple[ServerListEntry, ...]:
        self.poll()
        lan_entries = tuple(
            self._entry_from_discovered(server)
            for server in self._browser.get_servers(now=self._runtime.now())
        )
        return self._book.entries_for_tab(tab, lan_entries=lan_entries)

    def all_entries(self) -> tuple[ServerListEntry, ...]:
        self.poll()
        lan_entries = tuple(
            self._entry_from_discovered(server)
            for server in self._browser.get_servers(now=self._runtime.now())
        )
        return self._book.all_entries(lan_entries=lan_entries)

    def add_favorite(self, entry: ServerListEntry):
        self._book.add_favorite(entry)

    def add_default_local_favorite(self) -> ServerListEntry:
        return self._book.add_manual_server("127.0.0.1", DEFAULT_GAME_PORT, name="Local Groundfire Server")

    def add_manual_server(self, target: str, *, name: str | None = None) -> ServerListEntry:
        host, port = parse_server_target(target)
        return self._book.add_manual_server(host, port, name=name)

    def update_entry(self, entry: ServerListEntry):
        self._book.update_entry(entry)

    def record_history(self, entry: ServerListEntry):
        self._book.record_history(entry)

    def _entry_from_discovered(self, discovered: DiscoveredLanServer) -> ServerListEntry:
        announcement = discovered.announcement
        return ServerListEntry(
            name=announcement.server_name,
            host=discovered.address[0],
            port=int(announcement.server_port),
            game="Groundfire",
            map_name=f"seed {announcement.map_seed}",
            player_count=int(announcement.player_count),
            max_players=int(announcement.max_players),
            latency_ms=self._latency_hint(discovered),
            source="lan",
            description=self._description(announcement),
            requires_password=announcement.requires_password,
            region=announcement.region,
            secure=announcement.secure,
            protocol_version=PROTOCOL_VERSION,
        )

    def _latency_hint(self, discovered: DiscoveredLanServer) -> int:
        age_ms = int(max(0.0, self._runtime.now() - discovered.last_seen) * 1000.0)
        return min(999, age_ms)

    def _description(self, announcement: LanServerAnnouncement) -> str:
        locked = "password" if announcement.requires_password else "open"
        return f"Round {announcement.current_round} / {locked}"

    def _ping_latency(self, host: str, port: int, *, timeout: float) -> int | None:
        endpoint = DatagramEndpoint(host="", port=0)
        nonce = uuid.uuid4().hex
        issued_at = self._runtime.now()
        try:
            endpoint.sendto(encode_message(Ping(nonce=nonce, issued_at=issued_at)), (host, port))
            deadline = self._runtime.now() + timeout
            while self._runtime.now() <= deadline:
                for datagram in endpoint.poll(timeout=0.0):
                    try:
                        message = decode_message(datagram.payload)
                    except (ValueError, KeyError, TypeError):
                        continue
                    if isinstance(message, Pong) and message.nonce == nonce:
                        return int(max(0.0, self._runtime.now() - issued_at) * 1000.0)
                self._runtime.sleep(0.002)
        except OSError:
            return None
        finally:
            endpoint.close()
        return None


def default_server_book_path(project_root: str | Path) -> Path:
    return Path(project_root) / "conf" / "servers.json"


def default_master_server_addresses() -> tuple[MasterServerAddress, ...]:
    raw = os.environ.get("GROUNDFIRE_MASTER_SERVERS", f"127.0.0.1:{DEFAULT_MASTER_PORT}")
    addresses = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        addresses.append(parse_master_server_address(item))
    return tuple(addresses)


def parse_server_target(target: str) -> tuple[str, int]:
    raw = target.strip()
    if not raw:
        return "127.0.0.1", DEFAULT_GAME_PORT
    if ":" not in raw:
        return raw, DEFAULT_GAME_PORT
    host, raw_port = raw.rsplit(":", 1)
    host = host.strip() or "127.0.0.1"
    try:
        port = int(raw_port)
    except ValueError:
        port = DEFAULT_GAME_PORT
    if port < 1 or port > 65535:
        raise ValueError("Server port must be between 1 and 65535.")
    return host, port


def _normalize_master_servers(
    values: tuple[str | tuple[str, int] | MasterServerAddress, ...],
) -> tuple[MasterServerAddress, ...]:
    addresses = []
    for value in values:
        if isinstance(value, MasterServerAddress):
            addresses.append(value)
        elif isinstance(value, tuple):
            addresses.append(MasterServerAddress(str(value[0]), int(value[1])))
        else:
            addresses.append(parse_master_server_address(value))
    return tuple(addresses)


def _unique_entries(entries: tuple[ServerListEntry, ...]) -> tuple[ServerListEntry, ...]:
    seen: set[str] = set()
    unique = []
    for entry in entries:
        if entry.endpoint in seen:
            continue
        seen.add(entry.endpoint)
        unique.append(entry)
    return tuple(unique)
