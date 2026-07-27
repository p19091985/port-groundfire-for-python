from __future__ import annotations

from pathlib import Path
from typing import Callable

from groundfire_net.browser import ServerBook, ServerListEntry
from groundfire_net.transport import DatagramEndpoint

from ..core.headless import HeadlessRuntime
from ..network.browser import default_server_book_path
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
from ..render.scene import ReplicatedMatchScene, ReplicatedSceneRenderer
from .front import ConnectedFrontRuntime

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ClientApp:
    def __init__(
        self,
        *,
        runtime: HeadlessRuntime | None = None,
        game_factory: Callable[[], object] | None = None,
        legacy_game_factory: Callable[[], object] | None = None,
        network_backend: str = "udp",
        secure_server_public_key_path: str | Path | None = None,
        server_book_path: str | Path | None = None,
        event_logger: Callable[[str], None] | None = None,
    ):
        self._runtime = runtime or HeadlessRuntime()
        self._game_factory = game_factory or self._default_game_factory
        self._legacy_game_factory = legacy_game_factory or game_factory or self._default_legacy_game_factory
        self._network_backend = "udp"
        self._secure_server_public_key_path = (
            Path(secure_server_public_key_path) if secure_server_public_key_path else None
        )
        self._game = None
        self._legacy_game = None
        self._network_endpoint: DatagramEndpoint | None = None
        self._server_address: tuple[str, int] | None = None
        self._connected_computer_player = False
        self._hello_accept = None
        self._client_state = ClientReplicatedState()
        self._browser = LanServerBrowser()
        self._replicated_scene = ReplicatedMatchScene()
        self._scene_renderer = ReplicatedSceneRenderer()
        self._front_runtime = ConnectedFrontRuntime()
        self._event_logger = event_logger
        self._server_book_path = (
            Path(server_book_path)
            if server_book_path is not None
            else default_server_book_path(PROJECT_ROOT)
        )
        self._pending_history_entry: ServerListEntry | None = None
        self._last_logged_snapshot_phase: str | None = None

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
        if self._network_endpoint is not None:
            return self._network_endpoint.socket

        endpoint = DatagramEndpoint(host=host, port=port)
        self._network_endpoint = endpoint
        return endpoint.socket

    def close(self):
        self._send_disconnect_notice("client_closed")
        seen = set()
        for game in (self._game, self._legacy_game):
            if game is None or id(game) in seen:
                continue
            seen.add(id(game))
            close = getattr(game, "close", None)
            if callable(close):
                close()
        if self._network_endpoint is not None:
            self._network_endpoint.close()
            self._network_endpoint = None

    def reset_connection(self):
        self._send_disconnect_notice("return_to_menu")
        if self._network_endpoint is not None:
            self._network_endpoint.close()
            self._network_endpoint = None
        self._server_address = None
        self._connected_computer_player = False
        self._hello_accept = None
        self._pending_history_entry = None
        self._client_state = ClientReplicatedState()
        self._replicated_scene = ReplicatedMatchScene()
        self._last_logged_snapshot_phase = None
        self._log_network_event("connection_reset return_to_menu=true")

    def _send_disconnect_notice(self, reason: str):
        if self._network_endpoint is None or self._server_address is None:
            return
        session_id = self._client_state.session_id
        player_number = self._client_state.player_number
        session_token = self._client_state.session_token
        if session_id is None or player_number is None or session_token is None:
            return

        notice = DisconnectNotice(
            session_id=session_id,
            player_number=player_number,
            session_token=session_token,
            reason=reason,
        )
        try:
            self._network_endpoint.sendto(encode_message(notice), self._server_address)
        except OSError as exc:
            self._log_network_event(f"disconnect_notice_failed reason={reason} error={exc!r}")
            return
        self._log_network_event(f"disconnect_notice_sent player_number={player_number} reason={reason}")

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
        password: str = "",
        is_computer: bool = False,
        history_entry: ServerListEntry | None = None,
    ):
        self.open_network()
        self._server_address = (host, port)
        self._connected_computer_player = bool(is_computer)
        self._pending_history_entry = history_entry
        self._log_network_event(
            f"connecting host={host} port={port} player_name={player_name!r} computer={bool(is_computer)}"
        )
        messages = (
            HelloRequest(player_name=player_name),
            JoinRequest(
                player_name=player_name,
                requested_slot=requested_slot,
                password=password,
                is_computer=is_computer,
            ),
        )
        for message in messages:
            self.send_message(message)
        return messages

    def send_message(self, message):
        if self._network_endpoint is None or self._server_address is None:
            raise RuntimeError("Client network socket or server address is not initialized.")
        self._network_endpoint.sendto(encode_message(message), self._server_address)

    def poll_network(self, *, timeout: float = 0.0) -> tuple[object, ...]:
        if self._network_endpoint is None:
            return ()
        messages = []
        for datagram in self._network_endpoint.poll(timeout=timeout):
            messages.append(self.handle_packet(datagram.payload, datagram.address))
        return tuple(message for message in messages if message is not None)

    def handle_packet(self, payload: bytes, address: tuple[str, int]):
        return self._handle_message(decode_message(payload), address)

    def _handle_message(self, message, address: tuple[str, int]):
        if isinstance(message, JoinAccept):
            self._server_address = address
            self._client_state.apply_join_accept(message)
            self._log_network_event(
                f"join_accept player_number={message.player_number} session_id={message.session_id}"
            )
            self._record_pending_history()
        elif isinstance(message, JoinReject):
            self._client_state.apply_join_reject(message)
            self._log_network_event(f"join_reject reason={message.reason}")
            self._pending_history_entry = None
        elif isinstance(message, ServerSnapshotEnvelope):
            applied = self._client_state.apply_snapshot(message)
            if applied:
                self._log_snapshot_update(message)
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
            self._log_network_event(f"disconnect reason={message.reason or 'disconnected'}")
        elif isinstance(message, LanServerAnnouncement):
            self._browser.record_announcement(message, address, now=self._runtime.now())
        else:
            if hasattr(message, "server_name"):
                self._client_state.apply_hello_accept(message)
                self._log_network_event(
                    "hello_accept "
                    f"server_name={getattr(message, 'server_name')} "
                    f"players={getattr(message, 'player_count', '?')}/{getattr(message, 'max_players', '?')} "
                    f"requires_password={getattr(message, 'requires_password', False)}"
                )
            self._hello_accept = message
        return message

    def _record_pending_history(self):
        entry = self._pending_history_entry
        self._pending_history_entry = None
        if entry is None:
            return
        ServerBook(self._server_book_path).record_history(entry)

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
        self._log_network_event(
            "local_classic_only "
            f"show_menu={str(show_menu).lower()} ai_players={ai_players} "
            f"num_rounds={num_rounds} max_frames={max_frames}"
        )
        return self.run_legacy_local(
            player_name=player_name,
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
        self._log_network_event(
            "legacy_local_start "
            f"max_frames={max_frames} player_name={player_name!r} "
            f"configured={str(menu_selection is not None).lower()}"
        )
        if menu_selection is not None:
            self._configure_legacy_game(game, player_name=player_name, menu_selection=menu_selection)
        frames = 0
        while max_frames is None or frames < max_frames:
            if not game.loop_once():
                self._log_network_event(f"legacy_local_stop frames={frames} reason=loop_returned_false")
                return 0
            frames += 1
            connect_request = self._consume_legacy_connect_request(game)
            if connect_request is not None:
                remaining_frames = None if max_frames is None else max(0, max_frames - frames)
                result = self._run_connected_from_classic_menu(
                    game,
                    connect_request,
                    player_name=player_name,
                    max_frames=remaining_frames,
                )
                if result == ConnectedFrontRuntime.RETURN_TO_MENU:
                    self.reset_connection()
                    self._return_legacy_to_main_menu(game)
                    continue
                return result
        self._log_network_event(f"legacy_local_stop frames={frames} reason=max_frames")
        return 0

    def run_connected(self, *, max_frames: int | None = None) -> int:
        game = self.get_game()
        if not self._connected_computer_player:
            return self._front_runtime.run(self, game, max_frames=max_frames)
        return self._front_runtime.run(
            self,
            game,
            max_frames=max_frames,
            send_local_commands=not self._connected_computer_player,
        )

    def run_headless_connected(
        self,
        *,
        join_timeout: float = 5.0,
        keepalive_seconds: float = 0.0,
        poll_interval: float = 0.02,
    ) -> int:
        join_deadline = self._runtime.now() + max(0.0, join_timeout)
        self._log_network_event(f"headless_wait_for_join timeout={join_timeout:.3f}s")

        while self._runtime.now() <= join_deadline:
            self.poll_network(timeout=poll_interval)
            if self._client_state.join_reject_reason:
                return 2
            if self._client_state.session_id is not None:
                break
            self._runtime.sleep(0.0)

        if self._client_state.session_id is None:
            self._log_network_event(f"join_timeout timeout={join_timeout:.3f}s")
            return 1

        self._log_network_event(
            f"headless_joined player_number={self._client_state.player_number} keepalive={keepalive_seconds:.3f}s"
        )

        keepalive_deadline = self._runtime.now() + max(0.0, keepalive_seconds)
        while self._runtime.now() < keepalive_deadline:
            self.poll_network(timeout=poll_interval)
            if self._client_state.disconnect_reason or self._client_state.join_reject_reason:
                return 2
            self._runtime.sleep(0.0)

        self._log_network_event("headless_complete")
        return 0

    def _default_game_factory(self):
        from .shell import CanonicalClientShell

        return CanonicalClientShell()

    def _default_legacy_game_factory(self):
        from src.game import Game

        return Game()

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
            self._log_network_event("legacy_config target=controllers")
            self._change_legacy_state(game, game.GameState.CONTROLLERS_MENU)
            return

        if launch_target != "configured_start":
            self._log_network_event(f"legacy_config_skipped launch_target={launch_target!r}")
            return

        players_text = self._format_player_configs(getattr(menu_selection, "players", ()))
        self._log_network_event(
            "legacy_config target=configured_start "
            f"rounds={menu_selection.num_rounds} players={players_text}"
        )
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

        self._change_legacy_state(game, game.GameState.ROUND_STARTING)

    def _consume_legacy_connect_request(self, game):
        consume = getattr(game, "consume_online_connect_request", None)
        if not callable(consume):
            return None
        return consume()

    def _run_connected_from_classic_menu(
        self,
        game,
        request,
        *,
        player_name: str,
        max_frames: int | None,
    ) -> int:
        host = str(request.get("host", "127.0.0.1"))
        port = int(request.get("port", DEFAULT_GAME_PORT))
        password = str(request.get("password", ""))
        is_computer = bool(request.get("is_computer", False))
        entry = request.get("entry")
        enable_mouse = getattr(game.get_interface(), "enable_mouse", None)
        if callable(enable_mouse):
            enable_mouse(False)
        self.reset_connection()
        self.connect(
            host,
            port,
            player_name=player_name,
            password=password,
            is_computer=is_computer,
            history_entry=entry if isinstance(entry, ServerListEntry) else None,
        )
        self._log_network_event(f"legacy_local_connect host={host} port={port} computer={str(is_computer).lower()}")
        return self._front_runtime.run(
            self,
            game,
            max_frames=max_frames,
            send_local_commands=not is_computer,
        )

    def _return_legacy_to_main_menu(self, game):
        if hasattr(game, "GameState") and hasattr(game, "_change_state"):
            self._change_legacy_state(game, game.GameState.MAIN_MENU)

    def _change_legacy_state(self, game, new_state):
        previous_state = getattr(game, "_game_state", None)
        game._change_state(new_state)
        if hasattr(game, "_new_state"):
            game._new_state = new_state
        self._log_network_event(f"legacy_state_change previous={previous_state} new_state={new_state}")

    def _log_snapshot_update(self, envelope: ServerSnapshotEnvelope):
        snapshot = envelope.snapshot
        if snapshot.game_phase != self._last_logged_snapshot_phase:
            self._log_network_event(
                "snapshot_phase "
                f"sequence={envelope.snapshot_sequence} kind={envelope.snapshot_kind} "
                f"phase={snapshot.game_phase} round={snapshot.current_round}/{snapshot.num_rounds} "
                f"players={len(snapshot.players)} terrain_revision={snapshot.terrain_revision}"
            )
            self._last_logged_snapshot_phase = snapshot.game_phase
        if envelope.events:
            for event in envelope.events:
                self._log_network_event(f"server_event {self._format_server_event(event)}")
        if envelope.terrain_patches:
            self._log_network_event(
                "terrain_patches "
                f"sequence={envelope.snapshot_sequence} count={len(envelope.terrain_patches)}"
            )

    def _format_player_configs(self, players) -> str:
        configs = []
        for player in tuple(players or ()):
            kind = "human" if player.is_human else "cpu"
            configs.append(f"{player.slot}:{kind}:controller{player.controller}:{player.name}")
        return "[" + ",".join(configs) + "]"

    def _format_server_event(self, event: dict) -> str:
        event_type = str(event.get("event_type", "unknown"))
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            return f"event_type={event_type} payload={payload!r}"
        payload_text = " ".join(f"{key}={value!r}" for key, value in sorted(payload.items()))
        return f"event_type={event_type} {payload_text}".strip()

    def _log_network_event(self, message: str):
        if self._event_logger is not None:
            self._event_logger(message)
