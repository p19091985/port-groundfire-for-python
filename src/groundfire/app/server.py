from __future__ import annotations

import socket
from pathlib import Path

from groundfire_net.browser import ServerListEntry
from groundfire_net.master import MasterServerAddress, MasterServerClient, parse_master_server_address
from groundfire_net.server import NativeServerLoop, ServerLoopConfig
from groundfire_net.transport import DatagramEndpoint

from ..core.headless import HeadlessRuntime
from ..gameplay.match_controller import MatchController
from ..network.codec import decode_message, encode_message
from ..network.lan import LanDiscoveryService
from ..network.messages import (
    DEFAULT_DISCOVERY_PORT,
    DEFAULT_GAME_PORT,
    DisconnectNotice,
    HelloAccept,
    HelloRequest,
    JoinAccept,
    JoinReject,
    JoinRequest,
    Ping,
    Pong,
)


class ServerApp:
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = DEFAULT_GAME_PORT,
        discovery_port: int = DEFAULT_DISCOVERY_PORT,
        server_name: str = "Groundfire Server",
        map_seed: int = 1,
        max_players: int = 8,
        requires_password: bool = False,
        password: str = "",
        region: str = "world",
        secure: bool = True,
        master_servers: tuple[str | tuple[str, int] | MasterServerAddress, ...] = (),
        master_interval_seconds: float = 5.0,
        runtime: HeadlessRuntime | None = None,
        controller: MatchController | None = None,
        enable_discovery: bool = True,
        network_backend: str = "udp",
        secure_private_key_path: str | Path | None = None,
        secure_public_key_path: str | Path | None = None,
    ):
        self._host = host
        self._port = port
        self._discovery_port = discovery_port
        self._server_name = server_name
        self._map_seed = map_seed
        self._max_players = max_players
        self._password = password
        self._requires_password = bool(requires_password or password)
        self._region = region or "world"
        self._secure = bool(secure)
        self._master_servers = _normalize_master_servers(master_servers)
        self._master_interval_seconds = master_interval_seconds
        self._runtime = runtime or HeadlessRuntime()
        self._controller = controller or MatchController(seed=map_seed, max_players=max_players)
        self._enable_discovery = enable_discovery
        self._network_backend = "udp"
        self._secure_private_key_path = Path(secure_private_key_path) if secure_private_key_path else None
        self._secure_public_key_path = Path(secure_public_key_path) if secure_public_key_path else None
        self._game_endpoint: DatagramEndpoint | None = None
        self._discovery_socket: socket.socket | None = None
        self._lan = LanDiscoveryService()
        self._master_client = MasterServerClient()
        self._last_announcement_time = 0.0
        self._last_master_publish_time = 0.0

    def get_match_controller(self) -> MatchController:
        return self._controller

    def open(self):
        if self._game_endpoint is None:
            self._game_endpoint = DatagramEndpoint(host=self._host, port=self._port)

        if self._enable_discovery and self._discovery_port > 0 and self._discovery_socket is None:
            self._discovery_socket = self._lan.open_broadcast_socket()

        self._publish_to_master(force=True)
        return self

    def close(self):
        self._unregister_from_master()
        if self._game_endpoint is not None:
            self._game_endpoint.close()
            self._game_endpoint = None
        if self._discovery_socket is not None:
            self._discovery_socket.close()
        self._discovery_socket = None
        self._master_client.close()

    def get_bound_port(self) -> int:
        if self._game_endpoint is None:
            return self._port
        return self._game_endpoint.get_bound_port()

    def poll_network(self, *, timeout: float = 0.0) -> tuple[object, ...]:
        if self._game_endpoint is None:
            return ()
        responses: list[object] = []
        for datagram in self._game_endpoint.poll(timeout=timeout):
            responses.extend(self.handle_packet(datagram.payload, datagram.address))
        return tuple(responses)

    def handle_packet(self, payload: bytes, address: tuple[str, int]) -> tuple[object, ...]:
        return self.handle_message(decode_message(payload), address)

    def handle_message(self, message, address: tuple[str, int]) -> tuple[object, ...]:
        responses: list[object] = []

        if isinstance(message, HelloRequest):
            responses.append(
                HelloAccept(
                    session_id=self._controller.match_state.session_id,
                    server_name=self._server_name,
                    current_round=self._controller.match_state.current_round,
                    player_count=len(self._controller.match_state.player_slots),
                    max_players=self._max_players,
                    map_seed=self._map_seed,
                    requires_password=self._requires_password,
                    region=self._region,
                    secure=self._secure,
                )
            )
        elif isinstance(message, JoinRequest):
            if self._requires_password and message.password != self._password:
                reason = "password_required" if not message.password else "bad_password"
                responses.append(
                    JoinReject(
                        reason=reason,
                        session_id=self._controller.match_state.session_id,
                    )
                )
                for response in responses:
                    self._send(response, address)
                return tuple(responses)
            joined = self._controller.join_player(
                message.player_name,
                requested_slot=message.requested_slot,
                address=address,
            )
            if joined is None:
                responses.append(
                    JoinReject(
                        reason="server_full_or_slot_unavailable",
                        session_id=self._controller.match_state.session_id,
                    )
                )
            else:
                player, token = joined
                responses.append(
                    JoinAccept(
                        session_id=self._controller.match_state.session_id,
                        player_number=player.player_number,
                        session_token=token.token,
                    )
                )
        elif isinstance(message, Ping):
            responses.append(Pong(nonce=message.nonce, issued_at=message.issued_at))
        elif isinstance(message, DisconnectNotice):
            self._controller.disconnect_player(message.player_number, session_token=message.session_token)
        else:
            self._controller.remember_player_address(getattr(message, "player_number", -1), address)
            self._controller.apply_command_envelope(message)

        for response in responses:
            self._send(response, address)
        return tuple(responses)

    def step(self) -> tuple[object, ...]:
        self._controller.step()
        broadcasts: list[object] = []

        if self._controller.should_emit_snapshot():
            snapshot = self._controller.build_snapshot_envelope()
            if snapshot.events:
                event_envelope = self._controller.build_event_envelope(snapshot.events)
                if event_envelope is not None:
                    broadcasts.append(event_envelope)
            broadcasts.append(snapshot)
            for message in broadcasts:
                self._broadcast(message)

        now = self._runtime.now()
        if self._enable_discovery and (now - self._last_announcement_time) >= self._lan.DEFAULT_INTERVAL_SECONDS:
            announcement = self._lan.build_announcement(
                self._controller.match_state,
                server_name=self._server_name,
                map_seed=self._map_seed,
                max_players=self._max_players,
                requires_password=self._requires_password,
                server_port=self.get_bound_port(),
                region=self._region,
                secure=self._secure,
            )
            self._broadcast_announcement(announcement)
            broadcasts.append(announcement)
            self._last_announcement_time = now

        self._publish_to_master()
        return tuple(broadcasts)

    def run(self, *, max_ticks: int | None = None) -> int:
        self.open()
        loop = NativeServerLoop(
            poll_network=lambda: self.poll_network(timeout=0.0),
            step_simulation=lambda: self.step(),
            now=self._runtime.now,
            sleep=self._runtime.sleep,
        )
        return loop.run(ServerLoopConfig(tick_hz=float(self._controller.simulation_hz), max_ticks=max_ticks))

    def _send(self, message, address: tuple[str, int]):
        if self._game_endpoint is not None:
            self._game_endpoint.sendto(encode_message(message), address)

    def _broadcast(self, message):
        for address in self._controller.get_player_addresses():
            self._send(message, address)

    def _broadcast_announcement(self, announcement):
        if self._discovery_socket is None or self._discovery_port <= 0:
            return
        self._lan.broadcast(self._discovery_socket, announcement, port=self._discovery_port)

    def _maybe_broadcast_lan_announcement(self):
        if not self._enable_discovery:
            return
        now = self._runtime.now()
        if (now - self._last_announcement_time) < self._lan.DEFAULT_INTERVAL_SECONDS:
            return
        announcement = self._lan.build_announcement(
            self._controller.match_state,
            server_name=self._server_name,
            map_seed=self._map_seed,
            max_players=self._max_players,
            requires_password=self._requires_password,
            server_port=self.get_bound_port(),
            region=self._region,
            secure=self._secure,
        )
        self._broadcast_announcement(announcement)
        self._last_announcement_time = now

    def _publish_to_master(self, *, force: bool = False):
        if not self._master_servers:
            return
        now = self._runtime.now()
        if not force and (now - self._last_master_publish_time) < self._master_interval_seconds:
            return
        entry = self._build_master_entry()
        for address in self._master_servers:
            try:
                self._master_client.register(address, entry, timeout=0.02)
            except OSError:
                continue
        self._last_master_publish_time = now

    def _unregister_from_master(self):
        if not self._master_servers:
            return
        host = self._advertised_host()
        port = self.get_bound_port()
        for address in self._master_servers:
            try:
                self._master_client.unregister(address, host=host, port=port, timeout=0.01)
            except OSError:
                continue

    def _build_master_entry(self) -> ServerListEntry:
        player_count = len(self._controller.match_state.player_slots)
        locked = "password" if self._requires_password else "open"
        return ServerListEntry(
            name=self._server_name,
            host=self._advertised_host(),
            port=self.get_bound_port(),
            game="Groundfire",
            map_name=f"seed {self._map_seed}",
            player_count=player_count,
            max_players=self._max_players,
            latency_ms=None,
            source="internet",
            description=f"Round {self._controller.match_state.current_round} / {locked} / {self._region}",
            requires_password=self._requires_password,
            region=self._region,
            secure=self._secure,
        )

    def _advertised_host(self) -> str:
        if self._host in {"", "0.0.0.0", "::"}:
            return ""
        return self._host


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
