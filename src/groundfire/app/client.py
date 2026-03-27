from __future__ import annotations

import selectors
import socket
from pathlib import Path
from typing import Callable

from ..core.headless import HeadlessRuntime
from ..core.settings import set_ini_value
from ..network.client_state import ClientReplicatedState
from ..network.codec import decode_message, encode_message
from ..network.lan import LanServerBrowser
from ..network.messages import (
    DEFAULT_GAME_PORT,
    DisconnectNotice,
    HelloRequest,
    JoinAccept,
    JoinReject,
    JoinRequest,
    LanServerAnnouncement,
    ServerEventEnvelope,
    ServerSnapshotEnvelope,
)
from ..network.mpgameserver_backend import MpGameServerClientTransport
from ..render.scene import ReplicatedMatchScene, ReplicatedSceneRenderer
from .front import ConnectedFrontRuntime
from .local import LocalFrontRuntime


class ClientApp:
    def __init__(
        self,
        *,
        runtime: HeadlessRuntime | None = None,
        game_factory: Callable[[], object] | None = None,
        legacy_game_factory: Callable[[], object] | None = None,
        local_runtime: LocalFrontRuntime | None = None,
        network_backend: str = "udp",
        secure_server_public_key_path: str | Path | None = None,
    ):
        self._runtime = runtime or HeadlessRuntime()
        self._game_factory = game_factory or self._default_game_factory
        self._legacy_game_factory = legacy_game_factory or game_factory or self._default_legacy_game_factory
        self._network_backend = network_backend
        self._secure_server_public_key_path = (
            Path(secure_server_public_key_path) if secure_server_public_key_path else None
        )
        self._game = None
        self._legacy_game = None
        self._selector = selectors.DefaultSelector()
        self._socket: socket.socket | None = None
        self._secure_transport: MpGameServerClientTransport | None = None
        self._server_address: tuple[str, int] | None = None
        self._hello_accept = None
        self._client_state = ClientReplicatedState()
        self._browser = LanServerBrowser()
        self._replicated_scene = ReplicatedMatchScene()
        self._scene_renderer = ReplicatedSceneRenderer()
        self._front_runtime = ConnectedFrontRuntime()
        self._local_runtime = local_runtime or LocalFrontRuntime()

    def get_game(self):
        if self._game is None:
            self._game = self._game_factory()
        return self._game

    def get_legacy_game(self):
        if self._legacy_game is None:
            self._legacy_game = self._legacy_game_factory()
        return self._legacy_game

    def get_client_state(self) -> ClientReplicatedState:
        return self._client_state

    def get_browser(self) -> LanServerBrowser:
        return self._browser

    def get_replicated_scene(self) -> ReplicatedMatchScene:
        return self._replicated_scene

    def open_network(self, *, host: str = "0.0.0.0", port: int = 0):
        if self._socket is not None:
            return self._socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        sock.setblocking(False)
        self._selector.register(sock, selectors.EVENT_READ)
        self._socket = sock
        return sock

    def close(self):
        seen = set()
        for game in (self._game, self._legacy_game):
            if game is None or id(game) in seen:
                continue
            seen.add(id(game))
            close = getattr(game, "close", None)
            if callable(close):
                close()
        if self._secure_transport is not None:
            self._secure_transport.close()
            self._secure_transport = None
        if self._socket is not None:
            try:
                self._selector.unregister(self._socket)
            except Exception:
                pass
            self._socket.close()
            self._socket = None

    def close_game(self):
        self._close_game_instance("_game")

    def close_legacy_game(self):
        self._close_game_instance("_legacy_game")

    def connect(
        self,
        host: str,
        port: int = DEFAULT_GAME_PORT,
        *,
        player_name: str = "Player",
        requested_slot: int | None = None,
    ):
        if self._network_backend == "mpgameserver":
            self._server_address = (host, port)
            self._secure_transport = self._build_secure_transport()
            self._secure_transport.connect(
                host,
                port,
                player_name=player_name,
                requested_slot=requested_slot,
            )
            return ()
        self.open_network()
        self._server_address = (host, port)
        messages = (
            HelloRequest(player_name=player_name),
            JoinRequest(player_name=player_name, requested_slot=requested_slot),
        )
        for message in messages:
            self.send_message(message)
        return messages

    def send_message(self, message):
        if self._network_backend == "mpgameserver":
            if self._secure_transport is None:
                raise RuntimeError("Secure client transport is not initialized.")
            reliable = isinstance(message, (HelloRequest, JoinRequest, DisconnectNotice))
            self._secure_transport.send_message(message, reliable=reliable)
            return
        if self._socket is None or self._server_address is None:
            raise RuntimeError("Client network socket or server address is not initialized.")
        self._socket.sendto(encode_message(message), self._server_address)

    def poll_network(self, *, timeout: float = 0.0) -> tuple[object, ...]:
        if self._network_backend == "mpgameserver":
            if self._secure_transport is None:
                return ()
            messages = [
                self._handle_message(message, self._server_address or ("0.0.0.0", DEFAULT_GAME_PORT))
                for message in self._secure_transport.poll_messages()
            ]
            disconnect_reason = self._secure_transport.disconnect_reason
            if disconnect_reason and self._client_state.disconnect_reason is None:
                self._client_state.apply_disconnect(
                    DisconnectNotice(
                        session_id=self._client_state.session_id or "",
                        player_number=self._client_state.player_number or -1,
                        session_token=self._client_state.session_token or "",
                        reason=disconnect_reason,
                    )
                )
            return tuple(message for message in messages if message is not None)

        messages = []
        for key, _mask in self._selector.select(timeout):
            sock = key.fileobj
            try:
                while True:
                    payload, address = sock.recvfrom(65535)  # type: ignore[union-attr]
                    messages.append(self.handle_packet(payload, address))
            except BlockingIOError:
                continue
        return tuple(message for message in messages if message is not None)

    def handle_packet(self, payload: bytes, address: tuple[str, int]):
        return self._handle_message(decode_message(payload), address)

    def _handle_message(self, message, address: tuple[str, int]):
        if isinstance(message, JoinAccept):
            self._server_address = address
            self._client_state.apply_join_accept(message)
        elif isinstance(message, JoinReject):
            self._client_state.apply_join_reject(message)
        elif isinstance(message, ServerSnapshotEnvelope):
            applied = self._client_state.apply_snapshot(message)
            if applied:
                render_snapshot = self._client_state.get_render_snapshot()
                if render_snapshot is not None:
                    self._replicated_scene.apply_resolved_snapshot(
                        render_snapshot,
                        snapshot_sequence=message.snapshot_sequence,
                        terrain_patches=message.terrain_patches,
                        events=message.events,
                        local_player_number=self._client_state.player_number,
                        snapshot_kind=message.snapshot_kind,
                        baseline_snapshot_sequence=message.baseline_snapshot_sequence,
                        authoritative_snapshot=self._client_state.latest_snapshot,
                    )
        elif isinstance(message, ServerEventEnvelope):
            self._client_state.apply_events(message)
        elif isinstance(message, DisconnectNotice):
            self._client_state.apply_disconnect(message)
        elif isinstance(message, LanServerAnnouncement):
            self._browser.record_announcement(message, address, now=self._runtime.now())
        else:
            if hasattr(message, "server_name"):
                self._client_state.apply_hello_accept(message)
            self._hello_accept = message
        return message

    def build_and_send_command_envelope(self, commands: dict[str, bool], *, source: str = "client:local"):
        envelope = self._client_state.build_command_envelope(
            commands,
            issued_at=self._runtime.now(),
            source=source,
            simulation_tick=getattr(self._client_state.latest_snapshot, "simulation_tick", 0),
        )
        self.send_message(envelope)
        return envelope

    def apply_snapshot_envelope(self, envelope: ServerSnapshotEnvelope) -> bool:
        applied = self._client_state.apply_snapshot(envelope)
        if applied:
            render_snapshot = self._client_state.get_render_snapshot()
            if render_snapshot is not None:
                self._replicated_scene.apply_resolved_snapshot(
                    render_snapshot,
                    snapshot_sequence=envelope.snapshot_sequence,
                    terrain_patches=envelope.terrain_patches,
                    events=envelope.events,
                    local_player_number=self._client_state.player_number,
                    snapshot_kind=envelope.snapshot_kind,
                    baseline_snapshot_sequence=envelope.baseline_snapshot_sequence,
                    authoritative_snapshot=self._client_state.latest_snapshot,
                )
        return applied

    def build_remote_render_frame(self):
        return self._scene_renderer.build_frame(
            self._replicated_scene,
            local_player_number=self._client_state.player_number,
        )

    def render_remote_frame(self, game, frame):
        return self._scene_renderer.render_frame(
            game,
            frame,
            snapshot=self._replicated_scene.snapshot,
        )

    def render_connected_frame(self, game, frame=None):
        if frame is None:
            frame = self.build_remote_render_frame()
        return self.render_remote_frame(game, frame)

    def run_local(
        self,
        *,
        max_frames: int | None = None,
        player_name: str = "Player",
        ai_players: int = 1,
        num_rounds: int = 10,
        show_menu: bool = False,
    ) -> int:
        game = self.get_game()
        if show_menu:
            selection = self._local_runtime.open_menu(
                game,
                player_name=player_name,
                ai_players=ai_players,
                max_frames=max_frames,
            )
            if selection.action == "quit":
                return 0
            if selection.action == "classic":
                if selection.persist_mode:
                    self._persist_local_menu_mode(game, "classic")
                self.close_game()
                return self.run_legacy_local(
                    max_frames=max_frames,
                    player_name=player_name,
                    menu_selection=selection,
                )
            ai_players = selection.ai_players
            num_rounds = selection.num_rounds
            local_controller = selection.local_controller
            requested_slot = selection.requested_slot
            player_configs = selection.players
        else:
            local_controller = 0
            requested_slot = 0
            player_configs = ()
        return self._local_runtime.run(
            self,
            game,
            player_name=player_name,
            ai_players=ai_players,
            num_rounds=num_rounds,
            local_controller=local_controller,
            requested_slot=requested_slot,
            player_configs=player_configs,
            max_frames=max_frames,
        )

    def run_legacy_local(
        self,
        *,
        max_frames: int | None = None,
        player_name: str = "Player",
        ai_players: int = 1,
        menu_selection=None,
    ) -> int:
        game = self.get_legacy_game()
        if menu_selection is not None:
            self._configure_legacy_game(game, player_name=player_name, menu_selection=menu_selection)
        frames = 0
        while max_frames is None or frames < max_frames:
            if not game.loop_once():
                return 0
            frames += 1
        return 0

    def run_connected(self, *, max_frames: int | None = None) -> int:
        game = self.get_game()
        return self._front_runtime.run(self, game, max_frames=max_frames)

    def _default_game_factory(self):
        from .shell import CanonicalClientShell

        return CanonicalClientShell()

    def _default_legacy_game_factory(self):
        from src.game import Game

        return Game()

    def _build_secure_transport(self) -> MpGameServerClientTransport:
        if self._secure_server_public_key_path is None:
            raise RuntimeError("Secure online mode requires a trusted server public key path.")
        return MpGameServerClientTransport(public_key_path=self._secure_server_public_key_path)

    def _persist_local_menu_mode(self, game, mode: str):
        settings_path_getter = getattr(game, "get_settings_path", None)
        if not callable(settings_path_getter):
            return
        settings_path = settings_path_getter()
        try:
            set_ini_value(settings_path, "Interface", "LocalMenuMode", mode)
        except OSError:
            return

    def _close_game_instance(self, attr_name: str):
        game = getattr(self, attr_name, None)
        if game is None:
            return
        close = getattr(game, "close", None)
        if callable(close):
            close()
        setattr(self, attr_name, None)

    def _configure_legacy_game(self, game, *, player_name: str, menu_selection):
        if not hasattr(game, "GameState") or not hasattr(game, "_change_state"):
            return

        launch_target = getattr(menu_selection, "launch_target", None)
        if launch_target == "controllers":
            game._change_state(game.GameState.CONTROLLERS_MENU)
            return

        if launch_target != "configured_start":
            return

        if hasattr(game, "delete_players"):
            game.delete_players()
        if hasattr(game, "set_num_of_rounds"):
            game.set_num_of_rounds(menu_selection.num_rounds)

        players = tuple(getattr(menu_selection, "players", ()))
        named_local_player = False
        for player in players:
            controller = player.controller if player.is_human else -1
            name = player.name
            if player.is_human and not named_local_player and player_name:
                name = player_name
                named_local_player = True
            if hasattr(game, "add_player"):
                game.add_player(controller, name, player.colour)

        game._change_state(game.GameState.ROUND_STARTING)
