from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .codec import decode_message, encode_message
from .messages import (
    ClientCommandEnvelope,
    DisconnectNotice,
    HelloAccept,
    HelloRequest,
    JoinAccept,
    JoinReject,
    JoinRequest,
    Ping,
    Pong,
)

if TYPE_CHECKING:
    from ..core.headless import HeadlessRuntime
    from ..gameplay.match_controller import MatchController


class MpGameServerUnavailableError(RuntimeError):
    pass


def _load_mpgameserver():
    try:
        from mpgameserver import EventHandler, RetryMode, ServerContext, ThreadedServer, UdpClient
        from mpgameserver.crypto import EllipticCurvePrivateKey, EllipticCurvePublicKey
    except ImportError as exc:  # pragma: no cover - depends on optional dependency state
        raise MpGameServerUnavailableError(
            "mpgameserver is not installed. Install project dependencies to use the secure online backend."
        ) from exc
    return {
        "EventHandler": EventHandler,
        "RetryMode": RetryMode,
        "ServerContext": ServerContext,
        "ThreadedServer": ThreadedServer,
        "UdpClient": UdpClient,
        "EllipticCurvePrivateKey": EllipticCurvePrivateKey,
        "EllipticCurvePublicKey": EllipticCurvePublicKey,
    }


def ensure_server_keypair(
    private_key_path: str | Path,
    public_key_path: str | Path,
):
    api = _load_mpgameserver()
    private_cls = api["EllipticCurvePrivateKey"]

    private_path = Path(private_key_path)
    public_path = Path(public_key_path)
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    if private_path.exists():
        private_key = private_cls.fromPEM(private_path.read_text(encoding="utf-8"))
    else:
        private_key = private_cls.new()
        private_path.write_text(private_key.getPrivateKeyPEM(), encoding="utf-8")

    public_key = private_key.getPublicKey()
    public_pem = public_key.getPublicKeyPEM()
    if not public_path.exists() or public_path.read_text(encoding="utf-8") != public_pem:
        public_path.write_text(public_pem, encoding="utf-8")
    return private_key, public_key


def load_server_public_key(public_key_path: str | Path):
    api = _load_mpgameserver()
    public_cls = api["EllipticCurvePublicKey"]
    public_path = Path(public_key_path)
    if not public_path.exists():
        raise FileNotFoundError(
            f"Server public key not found at {public_path}. Refusing insecure secure-backend connection."
        )
    return public_cls.fromPEM(public_path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class SecureBackendPaths:
    server_private_key: Path
    server_public_key: Path


class MpGameServerClientTransport:
    def __init__(
        self,
        *,
        public_key_path: str | Path,
    ):
        self._api = _load_mpgameserver()
        self._public_key_path = Path(public_key_path)
        self._client = None
        self._pending_initial_messages: tuple[object, ...] = ()
        self._initial_messages_sent = False
        self._connect_succeeded = False
        self._connect_failed = False
        self._disconnect_reason: str | None = None
        self._reported_disconnect = False

    def connect(self, host: str, port: int, *, player_name: str, requested_slot: int | None = None):
        public_key = load_server_public_key(self._public_key_path)
        udp_client = self._api["UdpClient"](server_public_key=public_key)
        udp_client.connect((host, port), callback=self._on_connect_result)
        self._client = udp_client
        self._pending_initial_messages = (
            HelloRequest(player_name=player_name),
            JoinRequest(player_name=player_name, requested_slot=requested_slot),
        )
        self._initial_messages_sent = False
        self._connect_succeeded = False
        self._connect_failed = False
        self._disconnect_reason = None
        self._reported_disconnect = False

    def close(self):
        if self._client is None:
            return
        force_disconnect = getattr(self._client, "forceDisconnect", None)
        if callable(force_disconnect):
            force_disconnect()
        self._client = None

    def send_message(self, message, *, reliable: bool = False):
        if self._client is None:
            raise RuntimeError("Secure client transport is not connected.")
        retry = self._api["RetryMode"].RETRY_ON_TIMEOUT if reliable else self._api["RetryMode"].NONE
        self._client.send(encode_message(message), retry=retry)

    def poll_messages(self) -> tuple[object, ...]:
        if self._client is None:
            return ()

        self._client.update()
        self._send_initial_messages_if_ready()

        messages = []
        for _seqnum, payload in self._client.getMessages():
            messages.append(decode_message(payload))

        status = self._client.status()
        dropped_name = getattr(status, "name", str(status))
        if dropped_name in {"DISCONNECTED", "DROPPED"} and not self._reported_disconnect:
            if self._connect_failed:
                self._disconnect_reason = "secure_handshake_failed"
            else:
                self._disconnect_reason = self._disconnect_reason or "connection_dropped"
            self._reported_disconnect = True

        return tuple(messages)

    @property
    def disconnect_reason(self) -> str | None:
        return self._disconnect_reason

    def _on_connect_result(self, connected: bool):
        self._connect_succeeded = bool(connected)
        self._connect_failed = not connected
        if not connected:
            self._disconnect_reason = "secure_handshake_failed"

    def _send_initial_messages_if_ready(self):
        if self._client is None or self._initial_messages_sent:
            return
        if not self._client.connected():
            return
        for message in self._pending_initial_messages:
            self.send_message(message, reliable=True)
        self._initial_messages_sent = True


class _GroundfireSecureEventHandler:
    def __init__(
        self,
        *,
        controller: "MatchController",
        server_name: str,
        max_players: int,
    ):
        self._controller = controller
        self._server_name = server_name
        self._max_players = max_players
        self._connected_clients_by_token: dict[int, Any] = {}
        self._player_numbers_by_client_token: dict[int, int] = {}
        self.tick_count = 0
        self._retry_mode = _load_mpgameserver()["RetryMode"]

    def starting(self):
        return None

    def shutdown(self):
        return None

    def connect(self, client):
        self._connected_clients_by_token[client.token] = client

    def disconnect(self, client):
        self._connected_clients_by_token.pop(client.token, None)
        player_number = self._player_numbers_by_client_token.pop(client.token, None)
        if player_number is not None:
            self._controller.disconnect_player(player_number)

    def update(self, _delta_t: float):
        self.tick_count += 1
        self._controller.step()

        if not self._controller.should_emit_snapshot():
            return

        messages: list[object] = []
        snapshot = self._controller.build_snapshot_envelope()
        if snapshot.events:
            event_envelope = self._controller.build_event_envelope(snapshot.events)
            if event_envelope is not None:
                messages.append(event_envelope)
        messages.append(snapshot)

        for client in self._joined_clients():
            for message in messages:
                client.send(encode_message(message), retry=self._retry_mode.NONE)

    def handle_message(self, client, _seqnum, msg: bytes = b""):
        message = decode_message(msg)

        if isinstance(message, HelloRequest):
            client.send(
                encode_message(
                    HelloAccept(
                        session_id=self._controller.match_state.session_id,
                        server_name=self._server_name,
                        current_round=self._controller.match_state.current_round,
                        player_count=len(self._controller.match_state.player_slots),
                        max_players=self._max_players,
                    )
                ),
                retry=self._retry_mode.RETRY_ON_TIMEOUT,
            )
            return

        if isinstance(message, JoinRequest):
            existing_player = self._player_numbers_by_client_token.get(client.token)
            if existing_player is not None:
                player = self._controller.match_state.get_player(existing_player)
                token = self._controller._player_tokens.get(existing_player)
                if player is not None and token is not None:
                    client.send(
                        encode_message(
                            JoinAccept(
                                session_id=self._controller.match_state.session_id,
                                player_number=player.player_number,
                                session_token=token.token,
                            )
                        ),
                        retry=self._retry_mode.RETRY_ON_TIMEOUT,
                    )
                return

            joined = self._controller.join_player(
                message.player_name,
                requested_slot=message.requested_slot,
            )
            if joined is None:
                client.send(
                    encode_message(
                        JoinReject(
                            reason="server_full_or_slot_unavailable",
                            session_id=self._controller.match_state.session_id,
                        )
                    ),
                    retry=self._retry_mode.RETRY_ON_TIMEOUT,
                )
                return

            player, token = joined
            self._player_numbers_by_client_token[client.token] = player.player_number
            client.send(
                encode_message(
                    JoinAccept(
                        session_id=self._controller.match_state.session_id,
                        player_number=player.player_number,
                        session_token=token.token,
                    )
                ),
                retry=self._retry_mode.RETRY_ON_TIMEOUT,
            )
            return

        if isinstance(message, Ping):
            client.send(
                encode_message(Pong(nonce=message.nonce, issued_at=message.issued_at)),
                retry=self._retry_mode.NONE,
            )
            return

        if isinstance(message, DisconnectNotice):
            bound_player_number = self._player_numbers_by_client_token.get(client.token)
            if bound_player_number == message.player_number:
                if self._controller.disconnect_player(message.player_number, session_token=message.session_token):
                    self._player_numbers_by_client_token.pop(client.token, None)
            return

        if isinstance(message, ClientCommandEnvelope):
            bound_player_number = self._player_numbers_by_client_token.get(client.token)
            if bound_player_number != message.player_number:
                return
            self._controller.apply_command_envelope(message)

    def _joined_clients(self):
        seen_tokens = set()
        ordered_clients = []
        ordered_pairs = sorted(self._player_numbers_by_client_token.items(), key=lambda item: item[1])
        for client_token, player_number in ordered_pairs:
            if client_token in seen_tokens:
                continue
            client = self._connected_clients_by_token.get(client_token)
            if client is None:
                continue
            seen_tokens.add(client_token)
            ordered_clients.append(client)
        return tuple(ordered_clients)


class MpGameServerServerRuntime:
    def __init__(
        self,
        *,
        runtime: "HeadlessRuntime",
        controller: "MatchController",
        host: str,
        port: int,
        server_name: str,
        max_players: int,
        private_key_path: str | Path,
        public_key_path: str | Path,
    ):
        self._api = _load_mpgameserver()
        self._runtime = runtime
        self._controller = controller
        self._host = host
        self._port = port
        self._server_name = server_name
        self._max_players = max_players
        self._private_key_path = Path(private_key_path)
        self._public_key_path = Path(public_key_path)
        self._handler = _GroundfireSecureEventHandler(
            controller=controller,
            server_name=server_name,
            max_players=max_players,
        )
        self._context = None
        self._server = None

    @property
    def handler(self) -> _GroundfireSecureEventHandler:
        return self._handler

    @property
    def is_running(self) -> bool:
        return bool(self._server is not None and self._server.is_alive())

    def start(self):
        if self._server is not None:
            return
        private_key, _public_key = ensure_server_keypair(self._private_key_path, self._public_key_path)
        context = self._api["ServerContext"](self._handler, root_key=private_key)
        context.setInterval(1.0 / float(self._controller.simulation_hz))
        self._context = context
        self._server = self._api["ThreadedServer"](context, (self._host, self._port))
        self._server.start()

    def run(self, *, max_ticks: int | None = None) -> int:
        self.start()
        if self._server is None:
            return 0

        try:
            while self._server.is_alive():
                if max_ticks is not None and self._handler.tick_count >= max_ticks:
                    break
                self._runtime.sleep(0.01)
        finally:
            self.stop()
        return 0

    def stop(self):
        server = self._server
        self._server = None
        if server is not None:
            server.stop()
