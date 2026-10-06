from __future__ import annotations

import asyncio
import os
import signal
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

from fastapi import Depends, FastAPI, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from groundfire_net.directory_service import (
    SessionTokenError,
    directory_diagnostics,
    issue_session_token,
    load_directory_payload,
    response_bytes,
    response_etag,
)

from .compatibility import LegacyMasterSupervisor, directory_config
from .config import Settings, load_settings
from .console import console_router
from .domain import GroundfireService
from .errors import ServiceError
from .store import Store
from .workers import WorkerSpec, WorkerSupervisor


def create_app(settings: Settings | None = None) -> FastAPI:
    selected = settings or load_settings()
    service = GroundfireService(Store(selected.database_path), selected)
    supervisor = WorkerSupervisor(selected)
    legacy_directory_config = directory_config(selected)
    legacy_master = LegacyMasterSupervisor(selected)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        await asyncio.to_thread(legacy_master.start)
        try:
            yield
        finally:
            await asyncio.to_thread(supervisor.stop_all)
            await asyncio.to_thread(legacy_master.stop)

    app = FastAPI(title="Groundfire Online Service", version="0.2.0", lifespan=lifespan)
    app.state.service = service
    app.state.worker_supervisor = supervisor
    app.state.legacy_master = legacy_master
    app.include_router(console_router(selected, service, supervisor))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(selected.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "If-Match"],
        expose_headers=["ETag", "X-Request-ID", "Retry-After"],
    )

    @app.exception_handler(ServiceError)
    async def service_error_handler(_request: Request, exc: ServiceError) -> JSONResponse:
        headers = {"Retry-After": "1"} if exc.status in {429, 503} else {}
        return JSONResponse(
            status_code=exc.status,
            headers=headers,
            content={
                "error": {"code": exc.code, "message": exc.message, "retryable": exc.retryable, "details": exc.details},
                "request_id": _request_id(),
            },
        )

    def current(authorization: str | None = Header(default=None)) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise ServiceError(401, "authentication_required", "Autenticação obrigatória.")
        return service.authenticate(authorization[7:])

    async def allocate(prepared: dict, user_id: str) -> dict:
        if prepared["state"] == "active":
            return service.match(user_id, prepared["match_id"])
        spec = WorkerSpec(
            match_id=prepared["match_id"],
            lobby_id=prepared["lobby_id"],
            name=prepared["name"],
            rounds=prepared["rounds"],
            seed=prepared["seed"],
            capacity=prepared["capacity"],
            bots=prepared["bots"],
            password="",
            session_secret=prepared["session_secret"],
        )
        try:
            running = await asyncio.to_thread(supervisor.start, spec)
        except Exception as exc:
            service.fail_match(prepared["match_id"], "worker_start_failed")
            raise ServiceError(
                503,
                "worker_start_failed",
                "Não foi possível iniciar o servidor da partida.",
                retryable=True,
                details={"reason": str(exc)},
            ) from exc
        return service.activate_match(
            prepared["match_id"],
            {
                "udp_host": running.udp_host,
                "udp_port": running.udp_port,
                "websocket_url": running.websocket_url,
                "worker_pid": running.worker_pid,
                "gateway_pid": running.gateway_pid,
            },
        )

    async def body(request: Request) -> dict:
        try:
            value = await request.json()
        except Exception as exc:
            raise ServiceError(400, "invalid_json", "JSON inválido.") from exc
        if not isinstance(value, dict):
            raise ServiceError(400, "invalid_json", "O corpo precisa ser um objeto JSON.")
        return value

    @app.get("/health")
    @app.get("/healthz")
    def healthz() -> dict:
        return {
            "ok": True,
            "legacy_master": {
                "enabled": legacy_master.enabled,
                "running": legacy_master.running,
                "port": legacy_master.bound_port,
            },
        }

    @app.get("/readyz")
    def readyz() -> dict:
        service.store.one("SELECT 1")
        return {
            "ok": True,
            "schema": 1,
            "legacy_master_ready": not legacy_master.enabled or legacy_master.running,
        }

    @app.get("/api/v1/capabilities")
    def capabilities() -> dict:
        return _ok(service.capabilities())

    @app.post("/internal/v1/shutdown", status_code=202)
    async def request_shutdown(x_groundfire_control: str | None = Header(default=None)) -> dict:
        expected = os.environ.get("GF_SERVICE_CONTROL_NONCE", "")
        if not expected or x_groundfire_control != expected:
            raise ServiceError(401, "authentication_required", "Credencial de controle local obrigatória.")
        loop = asyncio.get_running_loop()
        loop.call_later(0.1, signal.raise_signal, signal.SIGINT)
        return _ok({"state": "draining"})

    def legacy_directory_payload() -> dict:
        # Managed rooms require REST admission and are intentionally not projected
        # as directly joinable protocol-1 servers.
        if not selected.legacy_directory_enabled:
            return {"schema": 1, "servers": []}
        return load_directory_payload(legacy_directory_config)

    @app.api_route("/", methods=["GET", "HEAD"])
    @app.api_route("/servers.json", methods=["GET", "HEAD"])
    def legacy_directory(request: Request) -> Response:
        encoded = response_bytes(legacy_directory_payload())
        etag = response_etag(encoded)
        validators = [part.strip() for part in request.headers.get("if-none-match", "").split(",")]
        headers = {
            "ETag": etag,
            "Cache-Control": f"public, max-age={legacy_directory_config.cache_seconds}, must-revalidate",
            "X-Groundfire-Directory-Refresh": str(legacy_directory_config.refresh_seconds),
            "Content-Length": str(len(encoded)),
        }
        if "*" in validators or etag in validators or etag.strip('"') in validators:
            return Response(status_code=304, headers=headers)
        return Response(
            b"" if request.method == "HEAD" else encoded,
            media_type="application/json",
            headers=headers,
        )

    @app.get("/schema.json")
    def legacy_schema() -> dict:
        return {
            "schema": 1,
            "required": {
                "name": "string",
                "game": "string",
                "players": "string",
                "map": "string",
                "latency": "string",
                "source": "string",
                "endpoint": "string",
                "passworded": "boolean",
            },
        }

    @app.get("/diagnostics.json")
    def diagnostics() -> dict:
        if not selected.legacy_directory_enabled:
            return {"ok": True, "schema": 1, "served_servers": 0, "legacy_disabled": True}
        result = directory_diagnostics(legacy_directory_config)
        result["managed_rooms_use_api"] = True
        return result

    @app.api_route("/session-token.json", methods=["GET", "HEAD"])
    def legacy_token(request: Request) -> Response:
        if not selected.legacy_directory_enabled or not legacy_directory_config.session_secret:
            payload = {"ok": False, "schema": 1, "error": "legacy_disabled"}
            encoded = response_bytes(payload)
            return Response(
                b"" if request.method == "HEAD" else encoded,
                status_code=HTTPStatus.GONE,
                media_type="application/json",
                headers={"Cache-Control": "no-store", "Content-Length": str(len(encoded))},
            )
        try:
            payload = issue_session_token(
                legacy_directory_config,
                request.query_params.get("player_name", ""),
                authorization=request.headers.get("authorization", ""),
            )
            status = HTTPStatus.OK
        except SessionTokenError as exc:
            payload = {"ok": False, "schema": 1, "error": exc.code}
            status = exc.status
        encoded = response_bytes(payload)
        return Response(
            b"" if request.method == "HEAD" else encoded,
            status_code=status,
            media_type="application/json",
            headers={"Cache-Control": "no-store", "Content-Length": str(len(encoded))},
        )

    @app.post("/api/v1/auth/register", status_code=201)
    async def register(request: Request) -> dict:
        data = await body(request)
        return _ok(
            service.register(
                str(data.get("handle", "")),
                str(data.get("display_name", "")),
                str(data.get("password", "")),
                str(data.get("device_name", "Groundfire")),
            )
        )

    @app.post("/api/v1/auth/guest", status_code=201)
    async def guest(request: Request) -> dict:
        data = await body(request)
        return _ok(service.guest(str(data.get("display_name", "Guest")), str(data.get("device_name", "Groundfire"))))

    @app.post("/api/v1/auth/login")
    async def login(request: Request) -> dict:
        data = await body(request)
        return _ok(
            service.login(
                str(data.get("handle", "")), str(data.get("password", "")), str(data.get("device_name", "Groundfire"))
            )
        )

    @app.post("/api/v1/auth/refresh")
    async def refresh(request: Request) -> dict:
        data = await body(request)
        return _ok(service.refresh(str(data.get("refresh_token", "")), str(data.get("device_name", "Groundfire"))))

    @app.post("/api/v1/auth/logout", status_code=204)
    def logout(session: dict = Depends(current)) -> None:
        service.logout(session["session_id"], session["user_id"])

    @app.get("/api/v1/me")
    def me(session: dict = Depends(current)) -> dict:
        return _ok(service.user(session["user_id"]))

    @app.put("/api/v1/me/presence")
    async def presence(request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(service.update_presence(session["user_id"], str(data.get("availability", "online"))))

    @app.get("/api/v1/friends")
    def friends(session: dict = Depends(current)) -> dict:
        return _ok({"items": service.list_friends(session["user_id"]), "next_cursor": None})

    @app.post("/api/v1/friend-requests", status_code=201)
    async def friend_request(request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(service.request_friend(session["user_id"], str(data.get("target_user_id", ""))))

    @app.post("/api/v1/friend-requests/{request_id}/accept")
    def friend_accept(request_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.accept_friend(session["user_id"], request_id))

    @app.put("/api/v1/blocks/{user_id}", status_code=204)
    def block(user_id: str, session: dict = Depends(current)) -> None:
        service.block(session["user_id"], user_id)

    @app.post("/api/v1/parties", status_code=201)
    def create_party(session: dict = Depends(current)) -> dict:
        return _ok(service.create_party(session["user_id"]))

    @app.get("/api/v1/parties/{party_id}")
    def get_party(party_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.party(session["user_id"], party_id))

    @app.post("/api/v1/parties/{party_id}/leave", status_code=204)
    def leave_party(party_id: str, session: dict = Depends(current)) -> None:
        service.leave_party(session["user_id"], party_id)

    @app.put("/api/v1/parties/{party_id}/members/me/ready")
    async def party_ready(party_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(
            service.set_party_ready(
                session["user_id"], party_id, int(data.get("revision", -1)), bool(data.get("ready", True))
            )
        )

    @app.get("/api/v1/lobbies")
    def list_lobbies() -> dict:
        return _ok({"items": service.list_lobbies(), "next_cursor": None})

    @app.get("/api/v1/servers")
    def list_servers() -> dict:
        return _ok({"items": service.list_servers(), "next_cursor": None})

    @app.post("/api/v1/lobbies", status_code=201)
    async def create_lobby(request: Request, session: dict = Depends(current)) -> dict:
        return _ok(service.create_lobby(session["user_id"], await body(request)))

    @app.get("/api/v1/lobbies/{lobby_id}")
    def get_lobby(lobby_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.lobby(session["user_id"], lobby_id))

    @app.post("/api/v1/lobbies/{lobby_id}/join")
    async def join_lobby(lobby_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(
            service.join_lobby(
                session["user_id"], lobby_id, str(data.get("password", "")), str(data.get("role", "player"))
            )
        )

    @app.post("/api/v1/lobbies/{lobby_id}/leave", status_code=204)
    def leave_lobby(lobby_id: str, session: dict = Depends(current)) -> None:
        service.leave_lobby(session["user_id"], lobby_id)

    @app.put("/api/v1/lobbies/{lobby_id}/members/me/ready")
    async def lobby_ready(lobby_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(
            service.set_lobby_ready(
                session["user_id"], lobby_id, int(data.get("revision", -1)), bool(data.get("ready", True))
            )
        )

    @app.post("/api/v1/lobbies/{lobby_id}/start", status_code=201)
    async def start_lobby(lobby_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        prepared = service.start_lobby(session["user_id"], lobby_id, int(data.get("revision", -1)))
        return _ok(await allocate(prepared, session["user_id"]))

    @app.post("/api/v1/invites", status_code=201)
    async def create_invite(request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(
            service.create_invite(
                session["user_id"],
                str(data.get("target_type", "")),
                str(data.get("target_id", "")),
                data.get("recipient_user_id"),
                int(data.get("max_uses", 1)),
            )
        )

    @app.post("/api/v1/invites/accept")
    async def accept_invite(request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(
            service.accept_invite(
                session["user_id"],
                invite_id=data.get("invite_id"),
                code=data.get("code"),
                password=str(data.get("password", "")),
            )
        )

    @app.post("/api/v1/matchmaking/queue", status_code=201)
    async def queue(request: Request, session: dict = Depends(current)) -> dict:
        return _ok(service.queue(session["user_id"], await body(request)))

    @app.post("/api/v1/servers/{server_id}/reservations", status_code=201)
    async def reserve_server(server_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(service.reserve_server(session["user_id"], server_id, password=str(data.get("password", ""))))

    @app.get("/api/v1/matchmaking/queue/{queue_id}")
    def queue_status(queue_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.queue_status(session["user_id"], queue_id))

    @app.delete("/api/v1/matchmaking/queue/{queue_id}", status_code=204)
    def queue_cancel(queue_id: str, session: dict = Depends(current)) -> None:
        service.cancel_queue(session["user_id"], queue_id)

    @app.get("/api/v1/reservations/{reservation_id}")
    def reservation(reservation_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.reservation(session["user_id"], reservation_id))

    @app.post("/api/v1/reservations/{reservation_id}/accept")
    async def reservation_accept(reservation_id: str, session: dict = Depends(current)) -> dict:
        result = service.accept_reservation(session["user_id"], reservation_id)
        match = None
        if result["state"] == "accepted":
            match = await allocate(service.prepare_allocation(reservation_id), session["user_id"])
            result = service.reservation(session["user_id"], reservation_id)
        return _ok({**result, "match": match})

    @app.post("/api/v1/reservations/{reservation_id}/admission-tickets")
    async def admission(reservation_id: str, request: Request, session: dict = Depends(current)) -> dict:
        data = await body(request)
        return _ok(service.admission_ticket(session["user_id"], reservation_id, str(data.get("transport", "wss"))))

    @app.get("/api/v1/matches/{match_id}")
    def match(match_id: str, session: dict = Depends(current)) -> dict:
        return _ok(service.match(session["user_id"], match_id))

    @app.post("/internal/v1/admissions/redeem")
    async def redeem(request: Request, x_groundfire_internal: str | None = Header(default=None)) -> dict:
        if x_groundfire_internal != "local-worker":
            raise ServiceError(401, "authentication_required", "Credencial interna obrigatória.")
        data = await body(request)
        return _ok(service.redeem_admission(str(data.get("ticket", ""))))

    @app.get("/api/v1/events")
    def event_poll(after: int = 0, limit: int = 100, session: dict = Depends(current)) -> dict:
        return _ok(service.events(session["user_id"], after, limit))

    @app.post("/api/v1/event-tickets")
    def event_ticket(session: dict = Depends(current)) -> dict:
        return _ok(service.issue_event_ticket(session["user_id"]))

    @app.get("/api/v1/channels/{channel_type}/{channel_id}/messages")
    def chat_history(
        channel_type: str,
        channel_id: str,
        after: int = 0,
        limit: int = 100,
        session: dict = Depends(current),
    ) -> dict:
        return _ok(service.chat_history(session["user_id"], channel_type, channel_id, after, limit))

    @app.post("/api/v1/channels/{channel_type}/{channel_id}/messages", status_code=201)
    async def send_chat(
        channel_type: str,
        channel_id: str,
        request: Request,
        session: dict = Depends(current),
    ) -> dict:
        data = await body(request)
        return _ok(
            service.send_chat(
                session["user_id"],
                channel_type,
                channel_id,
                str(data.get("text", "")),
                str(data.get("client_message_id", "")),
            )
        )

    @app.websocket("/api/v1/events/ws")
    async def event_socket(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            first = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            if first.get("type") != "auth" or int(first.get("protocol_version", 0)) != 1:
                await websocket.send_json({"type": "error", "code": "authentication_required"})
                await websocket.close(code=4401)
                return
            user_id = service.redeem_event_ticket(str(first.get("ticket", "")))
            cursor = int(first.get("resume_cursor") or 0)
            await websocket.send_json({"type": "authenticated", "protocol_version": 1, "cursor": str(cursor)})
            while True:
                batch = service.events(user_id, cursor, 100)
                for event in batch["items"]:
                    await websocket.send_json(event)
                    cursor = event["sequence"]
                try:
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong", "nonce": message.get("nonce")})
                    elif message.get("type") == "ack":
                        cursor = max(cursor, int(message.get("cursor", cursor)))
                    else:
                        await websocket.send_json({"type": "error", "code": "unsupported_message"})
                except TimeoutError:
                    pass
        except (WebSocketDisconnect, asyncio.TimeoutError):
            return
        except ServiceError as exc:
            await websocket.send_json({"type": "error", "code": exc.code, "message": exc.message})
            await websocket.close(code=4401)

    return app


def _ok(data: Any) -> dict:
    return {"data": data, "request_id": _request_id()}


def _request_id() -> str:
    return f"req_{uuid.uuid4().hex}"
