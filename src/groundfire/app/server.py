from __future__ import annotations

import socket
from pathlib import Path
from typing import Any, Callable

from groundfire_net.browser import ServerListEntry
from groundfire_net.master import MasterServerAddress, MasterServerClient, parse_master_server_address
from groundfire_net.server import NativeServerLoop, ServerLoopConfig
from groundfire_net.transport import DatagramEndpoint

from ..core.headless import HeadlessRuntime
from ..core.settings import ReadIniFile
from ..gameplay.match_controller import AIBehaviorConfig, MatchController
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
    RconCommand,
    RconResponse,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SETTINGS_PATH = PROJECT_ROOT / "conf" / "options.ini"


class ServerApp:
    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = DEFAULT_GAME_PORT,
        discovery_port: int = DEFAULT_DISCOVERY_PORT,
        server_name: str = "Groundfire Server",
        map_seed: int = 1,
        num_rounds: int = 10,
        max_players: int = 8,
        requires_password: bool = False,
        password: str = "",
        rcon_password: str = "",
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
        settings_path: str | Path = DEFAULT_SETTINGS_PATH,
        settings_loader: Callable[[str], Any] = ReadIniFile,
        event_logger: Callable[[str], None] | None = None,
    ):
        self._host = host
        self._port = port
        self._discovery_port = discovery_port
        self._server_name = server_name
        self._map_seed = map_seed
        self._num_rounds = num_rounds
        self._max_players = max_players
        self._password = password
        self._rcon_password = rcon_password
        self._requires_password = bool(requires_password or password)
        self._region = region or "world"
        self._secure = bool(secure)
        self._master_servers = _normalize_master_servers(master_servers)
        self._master_interval_seconds = master_interval_seconds
        self._runtime = runtime or HeadlessRuntime()
        self._settings_path = Path(settings_path)
        self._settings = settings_loader(str(self._settings_path))
        ai_config = AIBehaviorConfig.from_settings(self._settings)
        self._controller = controller or MatchController(
            seed=map_seed,
            num_rounds=num_rounds,
            max_players=max_players,
            ai_config=ai_config,
        )
        active_ai_config = getattr(self._controller, "_ai_config", ai_config)
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
        self._event_logger = event_logger
        self._last_logged_phase = self._controller.match_state.game_phase
        self._log_event(
            "server_config "
            f"name={self._quote(self._server_name)} host={self._host} port={self._port} "
            f"discovery_port={self._discovery_port} map_seed={self._map_seed} "
            f"rounds={self._num_rounds} max_players={self._max_players} "
            f"region={self._region} secure={str(self._secure).lower()} "
            f"password_required={str(self._requires_password).lower()} "
            f"rcon={self._enabled_label(self._rcon_password)} "
            f"master_servers={len(self._master_servers)} "
            f"ai_buy_special={str(active_ai_config.buy_special_weapons).lower()} "
            f"ai_use_special={str(active_ai_config.use_special_weapons).lower()}"
        )

    def get_match_controller(self) -> MatchController:
        return self._controller

    def open(self):
        if self._game_endpoint is None:
            self._log_event(f"server_open host={self._host} port={self._port}")
            try:
                self._game_endpoint = DatagramEndpoint(host=self._host, port=self._port)
            except OSError as exc:
                self._log_event(f"server_open_failed host={self._host} port={self._port} error={self._quote(exc)}")
                raise
            self._log_event(f"server_opened bound_port={self.get_bound_port()}")

        if self._enable_discovery and self._discovery_port > 0 and self._discovery_socket is None:
            self._log_event(f"lan_discovery_open port={self._discovery_port}")
            try:
                self._discovery_socket = self._lan.open_broadcast_socket()
            except OSError as exc:
                self._log_event(f"lan_discovery_open_failed port={self._discovery_port} error={self._quote(exc)}")
                raise

        self._publish_to_master(force=True)
        return self

    def close(self):
        self._log_event("server_close begin")
        self._unregister_from_master()
        if self._game_endpoint is not None:
            self._game_endpoint.close()
            self._game_endpoint = None
            self._log_event("game_endpoint_closed")
        if self._discovery_socket is not None:
            self._discovery_socket.close()
            self._log_event("lan_discovery_closed")
        self._discovery_socket = None
        self._master_client.close()
        self._log_event("server_close complete")

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
            self._log_event(f"hello_request player_name={self._quote(message.player_name)} address={address}")
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
            self._log_event(
                "join_request "
                f"player_name={self._quote(message.player_name)} requested_slot={message.requested_slot} "
                f"computer={str(message.is_computer).lower()} address={address} "
                f"password_present={str(bool(message.password)).lower()}"
            )
            if self._requires_password and message.password != self._password:
                reason = "password_required" if not message.password else "bad_password"
                self._log_event(
                    "join_reject "
                    f"player_name={self._quote(message.player_name)} reason={reason} address={address}"
                )
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
                is_computer=message.is_computer,
            )
            if joined is None:
                self._log_event(
                    "join_reject "
                    f"player_name={self._quote(message.player_name)} "
                    "reason=server_full_or_slot_unavailable "
                    f"requested_slot={message.requested_slot} address={address}"
                )
                responses.append(
                    JoinReject(
                        reason="server_full_or_slot_unavailable",
                        session_id=self._controller.match_state.session_id,
                    )
                )
            else:
                player, token = joined
                self._log_event(
                    "join_accept "
                    f"player_name={self._quote(player.name)} player_number={player.player_number} "
                    f"computer={str(player.is_computer).lower()} "
                    f"players={len(self._controller.match_state.player_slots)}/{self._max_players} "
                    f"phase={self._controller.match_state.game_phase} address={address}"
                )
                responses.append(
                    JoinAccept(
                        session_id=self._controller.match_state.session_id,
                        player_number=player.player_number,
                        session_token=token.token,
                    )
                )
        elif isinstance(message, Ping):
            self._log_event(f"ping nonce={self._quote(message.nonce)} address={address}")
            responses.append(Pong(nonce=message.nonce, issued_at=message.issued_at))
        elif isinstance(message, RconCommand):
            responses.append(self._handle_rcon_command(message, address=address))
        elif isinstance(message, DisconnectNotice):
            disconnected = self._controller.disconnect_player(message.player_number, session_token=message.session_token)
            self._log_event(
                "disconnect_notice "
                f"player_number={message.player_number} ok={str(disconnected).lower()} "
                f"reason={self._quote(message.reason or 'disconnected')} address={address}"
            )
        else:
            self._controller.remember_player_address(getattr(message, "player_number", -1), address)
            applied = self._controller.apply_command_envelope(message)
            self._log_client_command(message, address=address, applied=applied)

        for response in responses:
            self._send(response, address)
        return tuple(responses)

    def step(self) -> tuple[object, ...]:
        previous_phase = self._controller.match_state.game_phase
        self._controller.step()
        self._log_phase_change(previous_phase)
        broadcasts: list[object] = []

        if self._controller.should_emit_snapshot():
            snapshot = self._controller.build_snapshot_envelope()
            if snapshot.events or snapshot.terrain_patches or snapshot.removed_entity_ids or snapshot.removed_player_numbers:
                self._log_event(
                    "snapshot_emit "
                    f"sequence={snapshot.snapshot_sequence} kind={snapshot.snapshot_kind} "
                    f"tick={snapshot.simulation_tick} phase={snapshot.snapshot.game_phase} "
                    f"events={len(snapshot.events)} terrain_patches={len(snapshot.terrain_patches)} "
                    f"removed_entities={len(snapshot.removed_entity_ids)} "
                    f"removed_players={len(snapshot.removed_player_numbers)}"
                )
            for event in snapshot.events:
                self._log_match_event(event)
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
            self._log_event(
                "lan_announcement "
                f"server={self._quote(self._server_name)} port={self.get_bound_port()} "
                f"players={len(self._controller.match_state.player_slots)}/{self._max_players} "
                f"phase={self._controller.match_state.game_phase}"
            )

        self._publish_to_master()
        return tuple(broadcasts)

    def run(self, *, max_ticks: int | None = None) -> int:
        self.open()
        self._log_event(f"server_loop_start tick_hz={float(self._controller.simulation_hz):.1f} max_ticks={max_ticks}")
        loop = NativeServerLoop(
            poll_network=lambda: self.poll_network(timeout=0.0),
            step_simulation=lambda: self.step(),
            now=self._runtime.now,
            sleep=self._runtime.sleep,
        )
        try:
            result = loop.run(ServerLoopConfig(tick_hz=float(self._controller.simulation_hz), max_ticks=max_ticks))
        except Exception as exc:
            self._log_event(f"server_loop_error error={self._quote(exc)}")
            raise
        self._log_event(f"server_loop_stop result={result}")
        return result

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

    def _handle_rcon_command(self, message: RconCommand, *, address: tuple[str, int] | None = None) -> RconResponse:
        command = message.command.strip().lower()
        self._log_event(
            "rcon_command "
            f"command={self._quote(command or message.command)} request_id={self._quote(message.request_id)} "
            f"address={address} password_present={str(bool(message.password)).lower()}"
        )
        if not self._rcon_password:
            self._log_event(f"rcon_reject command={self._quote(command)} reason=rcon_disabled address={address}")
            return RconResponse(request_id=message.request_id, ok=False, output="rcon_disabled")
        if message.password != self._rcon_password:
            self._log_event(f"rcon_reject command={self._quote(command)} reason=bad_rcon_password address={address}")
            return RconResponse(request_id=message.request_id, ok=False, output="bad_rcon_password")

        if command in {"help", "?"}:
            output = "commands: status, players, start, help"
        elif command == "status":
            player_count = len(self._controller.match_state.player_slots)
            output = (
                f"name={self._server_name} "
                f"players={player_count}/{self._max_players} "
                f"phase={self._controller.match_state.game_phase} "
                f"can_start={str(self._controller.can_start_match()).lower()} "
                f"map=seed {self._map_seed} "
                f"round={self._controller.match_state.current_round}/{self._num_rounds} "
                f"region={self._region} "
                f"secure={str(self._secure).lower()}"
            )
        elif command == "players":
            players = tuple(
                self._controller.match_state.player_slots[player_number]
                for player_number in sorted(self._controller.match_state.player_slots)
            )
            output = "\n".join(f"{player.player_number}: {player.name}" for player in players) or "no_players"
        elif command in {"start", "start_match", "iniciar", "iniciar_partida"}:
            if self._controller.start_match(reason="rcon"):
                player_count = len(self._controller.match_state.player_slots)
                output = f"match_started players={player_count}/{self._max_players} round=1"
                self._log_event(
                    "rcon_start accepted "
                    f"players={player_count}/{self._max_players} phase={self._controller.match_state.game_phase}"
                )
            elif not self._controller.match_state.player_slots:
                output = "start_rejected: no_players"
                self._log_event("rcon_start rejected reason=no_players")
            else:
                output = f"start_rejected: phase={self._controller.match_state.game_phase}"
                self._log_event(f"rcon_start rejected phase={self._controller.match_state.game_phase}")
        else:
            self._log_event(f"rcon_reject command={self._quote(command)} reason=unknown_command address={address}")
            return RconResponse(request_id=message.request_id, ok=False, output=f"unknown_command: {command}")
        self._log_event(f"rcon_response command={self._quote(command)} ok=true output={self._quote(output)}")
        return RconResponse(request_id=message.request_id, ok=True, output=output)

    def _log_phase_change(self, previous_phase: str):
        current_phase = self._controller.match_state.game_phase
        if current_phase == self._last_logged_phase:
            return
        from_phase = self._last_logged_phase or previous_phase
        self._log_event(
            "phase_change "
            f"from={from_phase} to={current_phase} "
            f"round={self._controller.match_state.current_round}/{self._num_rounds} "
            f"tick={self._controller.match_state.simulation_tick}"
        )
        self._last_logged_phase = current_phase

    def _log_match_event(self, event: dict[str, Any]):
        event_type = str(event.get("event_type", "unknown"))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            payload = {"value": payload}
        payload_text = " ".join(f"{key}={self._quote(value)}" for key, value in sorted(payload.items()))
        suffix = f" {payload_text}" if payload_text else ""
        self._log_event(f"match_event event_type={event_type}{suffix}")

    def _log_client_command(self, message, *, address: tuple[str, int], applied: bool):
        commands = getattr(message, "commands", None)
        if not isinstance(commands, dict):
            self._log_event(
                "client_message "
                f"type={type(message).__name__} player_number={getattr(message, 'player_number', None)} "
                f"applied={str(applied).lower()} address={address}"
            )
            return
        active_commands = ",".join(sorted(str(name) for name, active in commands.items() if active))
        if not active_commands and applied:
            return
        self._log_event(
            "client_command "
            f"player_number={getattr(message, 'player_number', None)} "
            f"sequence={getattr(message, 'client_sequence', None)} "
            f"tick={getattr(message, 'simulation_tick', None)} "
            f"source={self._quote(getattr(message, 'source', 'unknown'))} "
            f"active={self._quote(active_commands or 'none')} "
            f"applied={str(applied).lower()} address={address}"
        )

    def _log_event(self, message: str):
        if self._event_logger is not None:
            self._event_logger(message)

    def _quote(self, value) -> str:
        text = str(value)
        if not text:
            return "''"
        safe = text.replace("\\", "\\\\").replace("'", "\\'")
        return f"'{safe}'" if any(char.isspace() for char in safe) else safe

    def _enabled_label(self, value: str) -> str:
        return "enabled" if value else "disabled"

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
                self._log_event(
                    "master_register "
                    f"address={address.host}:{address.port} "
                    f"players={entry.player_count}/{entry.max_players} phase={self._controller.match_state.game_phase}"
                )
            except OSError:
                self._log_event(f"master_register_failed address={address.host}:{address.port}")
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
                self._log_event(f"master_unregister address={address.host}:{address.port} host={host} port={port}")
            except OSError:
                self._log_event(f"master_unregister_failed address={address.host}:{address.port} host={host} port={port}")
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
