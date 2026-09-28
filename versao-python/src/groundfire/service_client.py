from __future__ import annotations

import json
import os
import queue
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


class ServiceClientError(RuntimeError):
    def __init__(self, code: str, message: str, *, status: int = 0, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.status = status
        self.retryable = retryable


@dataclass(frozen=True)
class ServiceResult:
    request_id: str
    data: Any


class GroundfireServiceClient:
    """HTTP adapter kept independent from the Pygame render loop."""

    def __init__(self, base_url: str | None = None, *, timeout: float = 5.0):
        self.base_url = (base_url or os.environ.get("GROUNDFIRE_SERVICE_URL", "http://127.0.0.1:27880")).rstrip("/")
        self.timeout = timeout
        self.access_token = ""
        self.refresh_token = ""
        self._completed: queue.SimpleQueue[
            tuple[Callable[[ServiceResult | None, Exception | None], None], ServiceResult | None, Exception | None]
        ] = queue.SimpleQueue()

    def request(self, method: str, path: str, body: dict | None = None, *, authenticated: bool = True) -> ServiceResult:
        payload = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        request = urllib.request.Request(f"{self.base_url}{path}", data=payload, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                error = json.loads(raw.decode("utf-8"))["error"]
            except (ValueError, KeyError, TypeError):
                raise ServiceClientError("http_error", f"HTTP {exc.code}", status=exc.code) from exc
            raise ServiceClientError(
                str(error.get("code", "http_error")),
                str(error.get("message", "Erro do serviço.")),
                status=exc.code,
                retryable=bool(error.get("retryable", False)),
            ) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise ServiceClientError("service_unavailable", str(exc), retryable=True) from exc
        if not raw:
            return ServiceResult("", None)
        decoded = json.loads(raw.decode("utf-8"))
        return ServiceResult(str(decoded.get("request_id", "")), decoded.get("data"))

    def submit(
        self,
        method: str,
        path: str,
        body: dict | None,
        callback: Callable[[ServiceResult | None, Exception | None], None],
        *,
        authenticated: bool = True,
    ) -> None:
        def worker() -> None:
            try:
                result, error = self.request(method, path, body, authenticated=authenticated), None
            except Exception as exc:  # delivered on the owning UI thread by poll()
                result, error = None, exc
            self._completed.put((callback, result, error))

        threading.Thread(target=worker, name="groundfire-service-request", daemon=True).start()

    def poll(self, *, limit: int = 32) -> int:
        delivered = 0
        while delivered < limit:
            try:
                callback, result, error = self._completed.get_nowait()
            except queue.Empty:
                break
            callback(result, error)
            delivered += 1
        return delivered

    def register(self, handle: str, display_name: str, password: str) -> dict:
        data = self.request(
            "POST",
            "/api/v1/auth/register",
            {"handle": handle, "display_name": display_name, "password": password},
            authenticated=False,
        ).data
        self._save_session(data)
        return data

    def login(self, handle: str, password: str) -> dict:
        data = self.request(
            "POST", "/api/v1/auth/login", {"handle": handle, "password": password}, authenticated=False
        ).data
        self._save_session(data)
        return data

    def guest(self, display_name: str) -> dict:
        data = self.request("POST", "/api/v1/auth/guest", {"display_name": display_name}, authenticated=False).data
        self._save_session(data)
        return data

    def create_lobby(self, **rules: Any) -> dict:
        return self.request("POST", "/api/v1/lobbies", rules).data

    def set_lobby_ready(self, lobby_id: str, revision: int, ready: bool = True) -> dict:
        encoded = urllib.parse.quote(lobby_id)
        return self.request(
            "PUT",
            f"/api/v1/lobbies/{encoded}/members/me/ready",
            {"revision": revision, "ready": ready},
        ).data

    def start_lobby(self, lobby_id: str, revision: int) -> dict:
        encoded = urllib.parse.quote(lobby_id)
        return self.request("POST", f"/api/v1/lobbies/{encoded}/start", {"revision": revision}).data

    def invite(self, target_type: str, target_id: str, recipient_user_id: str | None = None) -> dict:
        body = {"target_type": target_type, "target_id": target_id}
        if recipient_user_id:
            body["recipient_user_id"] = recipient_user_id
        return self.request("POST", "/api/v1/invites", body).data

    def accept_invite(self, code: str, password: str = "") -> dict:
        return self.request("POST", "/api/v1/invites/accept", {"code": code, "password": password}).data

    def accept_reservation(self, reservation_id: str) -> dict:
        encoded = urllib.parse.quote(reservation_id)
        return self.request("POST", f"/api/v1/reservations/{encoded}/accept", {}).data

    def admission_ticket(self, reservation_id: str, transport: str = "ws") -> dict:
        encoded = urllib.parse.quote(reservation_id)
        return self.request("POST", f"/api/v1/reservations/{encoded}/admission-tickets", {"transport": transport}).data

    def send_chat(self, channel_type: str, channel_id: str, text: str, client_message_id: str) -> dict:
        channel = urllib.parse.quote(channel_type)
        identifier = urllib.parse.quote(channel_id)
        return self.request(
            "POST",
            f"/api/v1/channels/{channel}/{identifier}/messages",
            {"text": text, "client_message_id": client_message_id},
        ).data

    def chat_history(self, channel_type: str, channel_id: str, after: int = 0) -> dict:
        channel = urllib.parse.quote(channel_type)
        identifier = urllib.parse.quote(channel_id)
        return self.request("GET", f"/api/v1/channels/{channel}/{identifier}/messages?after={after}").data

    def queue_match(
        self, *, party_id: str | None = None, party_revision: int | None = None, criteria: dict | None = None
    ) -> dict:
        body: dict[str, Any] = {"criteria": criteria or {}}
        if party_id:
            body.update({"party_id": party_id, "party_revision": party_revision})
        return self.request("POST", "/api/v1/matchmaking/queue", body).data

    def cancel_queue(self, queue_id: str) -> None:
        self.request("DELETE", f"/api/v1/matchmaking/queue/{urllib.parse.quote(queue_id)}")

    def _save_session(self, data: dict) -> None:
        self.access_token = str(data.get("access_token", ""))
        self.refresh_token = str(data.get("refresh_token", ""))
