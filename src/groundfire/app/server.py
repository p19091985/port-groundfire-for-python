from __future__ import annotations

import selectors
import socket
from pathlib import Path

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
from ..network.mpgameserver_backend import MpGameServerServerRuntime


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
        self._requires_password = requires_password
        self._runtime = runtime or HeadlessRuntime()
        self._controller = controller or MatchController(seed=map_seed, max_players=max_players)
        self._enable_discovery = enable_discovery
        self._network_backend = network_backend
        self._secure_private_key_path = Path(secure_private_key_path) if secure_private_key_path else None
        self._secure_public_key_path = Path(secure_public_key_path) if secure_public_key_path else None
        self._selector = selectors.DefaultSelector()
        self._game_socket: socket.socket | None = None
        self._discovery_socket: socket.socket | None = None
        self._secure_runtime: MpGameServerServerRuntime | None = None
        self._lan = LanDiscoveryService()
        self._last_announcement_time = 0.0

    def get_match_controller(self) -> MatchController:
        return self._controller

    def open(self):
        if self._network_backend == "mpgameserver":
            if self._enable_discovery and self._discovery_socket is None:
                self._discovery_socket = self._lan.open_broadcast_socket()
            return self

        if self._game_socket is None:
            game_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            game_socket.bind((self._host, self._port))
            game_socket.setblocking(False)
            self._selector.register(game_socket, selectors.EVENT_READ)
            self._game_socket = game_socket

        if self._enable_discovery and self._discovery_socket is None:
            self._discovery_socket = self._lan.open_broadcast_socket()

        return self

    def close(self):
        secure_runtime = self._secure_runtime
        self._secure_runtime = None
        if secure_runtime is not None:
            secure_runtime.stop()

        for sock in (self._game_socket, self._discovery_socket):
            if sock is None:
                continue
            try:
                self._selector.unregister(sock)
            except Exception:
                pass
            sock.close()
        self._game_socket = None
        self._discovery_socket = None

    def get_bound_port(self) -> int:
        if self._network_backend == "mpgameserver":
            return self._port
        if self._game_socket is None:
            return self._port
        return int(self._game_socket.getsockname()[1])

    def poll_network(self, *, timeout: float = 0.0) -> tuple[object, ...]:
        if self._network_backend == "mpgameserver":
            return ()
        responses: list[object] = []
        for key, _mask in self._selector.select(timeout):
            sock = key.fileobj
            try:
                while True:
                    payload, address = sock.recvfrom(65535)  # type: ignore[union-attr]
                    responses.extend(self.handle_packet(payload, address))
            except BlockingIOError:
                continue
        return tuple(responses)

    def handle_packet(self, payload: bytes, address: tuple[str, int]) -> tuple[object, ...]:
        if self._network_backend == "mpgameserver":
            return ()
        return self.handle_message(decode_message(payload), address)

    def handle_message(self, message, address: tuple[str, int]) -> tuple[object, ...]:
        if self._network_backend == "mpgameserver":
            return ()
        responses: list[object] = []

        if isinstance(message, HelloRequest):
            responses.append(
                HelloAccept(
                    session_id=self._controller.match_state.session_id,
                    server_name=self._server_name,
                    current_round=self._controller.match_state.current_round,
                    player_count=len(self._controller.match_state.player_slots),
                    max_players=self._max_players,
                )
            )
        elif isinstance(message, JoinRequest):
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
        if self._network_backend == "mpgameserver":
            return ()
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
            )
            self._broadcast_announcement(announcement)
            broadcasts.append(announcement)
            self._last_announcement_time = now

        return tuple(broadcasts)

    def run(self, *, max_ticks: int | None = None) -> int:
        if self._network_backend == "mpgameserver":
            self.open()
            secure_runtime = self._build_secure_runtime()
            self._secure_runtime = secure_runtime
            secure_runtime.start()
            try:
                while secure_runtime.is_running:
                    if max_ticks is not None and secure_runtime.handler.tick_count >= max_ticks:
                        break
                    self._maybe_broadcast_lan_announcement()
                    self._runtime.sleep(0.01)
            finally:
                self.close()
            return 0

        self.open()
        ticks = 0
        tick_duration = 1.0 / self._controller.simulation_hz

        while max_ticks is None or ticks < max_ticks:
            start = self._runtime.now()
            self.poll_network(timeout=0.0)
            self.step()
            ticks += 1
            elapsed = self._runtime.now() - start
            self._runtime.sleep(tick_duration - elapsed)

        return 0

    def _send(self, message, address: tuple[str, int]):
        if self._game_socket is not None:
            self._game_socket.sendto(encode_message(message), address)

    def _broadcast(self, message):
        for address in self._controller.get_player_addresses():
            self._send(message, address)

    def _broadcast_announcement(self, announcement):
        if self._discovery_socket is None:
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
        )
        self._broadcast_announcement(announcement)
        self._last_announcement_time = now

    def _build_secure_runtime(self) -> MpGameServerServerRuntime:
        if self._secure_private_key_path is None or self._secure_public_key_path is None:
            raise RuntimeError("Secure online mode requires server private and public key paths.")
        return MpGameServerServerRuntime(
            runtime=self._runtime,
            controller=self._controller,
            host=self._host,
            port=self._port,
            server_name=self._server_name,
            max_players=self._max_players,
            private_key_path=self._secure_private_key_path,
            public_key_path=self._secure_public_key_path,
        )
