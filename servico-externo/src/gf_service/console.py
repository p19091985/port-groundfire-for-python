"""Local operator console for the standalone service.

The public game API deliberately does not expose these operational details.
"""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import os
import secrets
import signal
import sqlite3
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse

from .config import Settings
from .domain import GroundfireService
from .workers import WorkerSupervisor


ASSETS = Path(__file__).resolve().parent / "ui"


def _is_loopback(value: str) -> bool:
    if value == "localhost":
        return True
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def console_router(settings: Settings, service: GroundfireService, supervisor: WorkerSupervisor) -> APIRouter:
    router = APIRouter()

    def guard(request: Request, *, authorized: bool = False) -> JSONResponse | None:
        # Disabling the console on a public bind prevents accidental exposure
        # through a reverse proxy, even when the proxy itself connects locally.
        if not _is_loopback(settings.bind):
            return JSONResponse({"error": "console_unavailable"}, status_code=404)
        peer = request.client.host if request.client else ""
        if not _is_loopback(peer):
            return JSONResponse({"error": "local_access_only"}, status_code=403)
        host = request.headers.get("host", "")
        configured_host = "[::1]" if settings.bind == "::1" else settings.bind
        if host not in {f"127.0.0.1:{settings.port}", f"localhost:{settings.port}", f"[::1]:{settings.port}", f"{configured_host}:{settings.port}"}:
            return JSONResponse({"error": "invalid_host"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin != f"http://{host}":
            return JSONResponse({"error": "invalid_origin"}, status_code=403)
        if authorized:
            expected = os.environ.get("GF_SERVICE_CONTROL_NONCE", "")
            supplied = request.headers.get("x-groundfire-control", "")
            if not expected or not secrets.compare_digest(supplied, expected):
                return JSONResponse({"error": "authentication_required"}, status_code=401)
        return None

    def asset(request: Request, name: str, media_type: str):
        rejected = guard(request)
        if rejected:
            return rejected
        return FileResponse(
            ASSETS / name,
            media_type=media_type,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    @router.get("/console", include_in_schema=False)
    def console(request: Request):
        rejected = guard(request)
        if rejected:
            return rejected
        return FileResponse(
            ASSETS / "index.html",
            media_type="text/html",
            headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'",
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.get("/console/assets/style.css", include_in_schema=False)
    def stylesheet(request: Request):
        return asset(request, "style.css", "text/css")

    @router.get("/console/assets/app.js", include_in_schema=False)
    def script(request: Request):
        return asset(request, "app.js", "text/javascript")

    @router.get("/console/api/snapshot", include_in_schema=False)
    def snapshot(request: Request):
        rejected = guard(request, authorized=True)
        if rejected:
            return rejected
        now = time.time()
        db = service.store
        count = lambda query, params=(): int(db.one(query, params)[0])
        metrics = {
            "users": count("SELECT COUNT(*) FROM users"),
            "online": count("SELECT COUNT(*) FROM presence WHERE expires_at>? AND availability='online'", (now,)),
            "lobbies": count("SELECT COUNT(*) FROM lobbies WHERE state='open'"),
            "queued": count("SELECT COUNT(*) FROM queue_tickets WHERE state='searching' AND expires_at>?", (now,)),
            "matches": count("SELECT COUNT(*) FROM matches WHERE state='active'"),
            "workers": supervisor.active_count(),
        }
        lobbies = [dict(row) for row in db.all(
            "SELECT l.lobby_id,l.name,l.visibility,l.state,l.capacity,l.rounds,l.map_id,l.bots,"
            "COUNT(lm.user_id) AS players FROM lobbies l LEFT JOIN lobby_members lm ON lm.lobby_id=l.lobby_id "
            "GROUP BY l.lobby_id ORDER BY l.created_at DESC LIMIT 30"
        )]
        matches = [dict(row) for row in db.all(
            "SELECT m.match_id,l.name,m.state,m.udp_port,m.worker_pid,m.gateway_pid,m.created_at,m.started_at,"
            "m.stopped_at,m.failure_code FROM matches m JOIN lobbies l ON l.lobby_id=m.lobby_id "
            "ORDER BY m.created_at DESC LIMIT 30"
        )]
        activity = [dict(row) for row in db.all(
            "SELECT event_type,resource_id,created_at FROM events ORDER BY sequence DESC LIMIT 25"
        )]
        return JSONResponse({
            "timestamp": now,
            "endpoint": f"http://{'[::1]' if settings.bind == '::1' else settings.bind}:{settings.port}",
            "database": settings.database_path.name,
            "worker_limit": settings.max_workers,
            "metrics": metrics,
            "lobbies": lobbies,
            "matches": matches,
            "activity": activity,
        }, headers={"Cache-Control": "no-store"})

    @router.post("/console/api/backup", include_in_schema=False)
    async def backup(request: Request):
        rejected = guard(request, authorized=True)
        if rejected:
            return rejected
        destination = await asyncio.to_thread(_backup_database, settings)
        return JSONResponse({"file": destination.name, "directory": str(destination.parent)}, headers={"Cache-Control": "no-store"})

    @router.post("/console/api/stop", include_in_schema=False)
    async def stop(request: Request):
        rejected = guard(request, authorized=True)
        if rejected:
            return rejected
        asyncio.get_running_loop().call_later(0.2, signal.raise_signal, signal.SIGINT)
        return JSONResponse({"state": "draining"}, status_code=202)

    return router


def _backup_database(settings: Settings) -> Path:
    target_dir = settings.root / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / f"groundfire-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}-{uuid.uuid4().hex[:8]}.sqlite3"
    source = sqlite3.connect(settings.database_path)
    target = sqlite3.connect(destination)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".json").write_text(
        json.dumps({"schema": 1, "database": destination.name, "sha256": digest}, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination
