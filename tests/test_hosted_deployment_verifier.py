from __future__ import annotations

import json
import subprocess
import sys
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qs, urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "verify_godot_hosted_deployment.py"


@dataclass(frozen=True)
class FixtureOptions:
    static_auth_token: bool = False
    token_no_store: bool = True
    etag: str = '"groundfire-directory-v1"'


def test_hosted_deployment_verifier_accepts_production_shaped_fixture():
    with _hosted_fixture() as base_url:
        completed = _run_verifier(
            "--allow-http",
            "--web-url",
            f"{base_url}/index.html",
            "--directory-url",
            f"{base_url}/directory/servers.json",
            "--health-url",
            f"{base_url}/directory/healthz",
            "--diagnostics-url",
            f"{base_url}/directory/diagnostics.json",
        )

    assert completed.returncode == 0, completed.stderr
    assert "[PASS] web export" in completed.stdout
    assert "[PASS] server directory" in completed.stdout
    assert "[PASS] optional hosted diagnostics" in completed.stdout


def test_hosted_deployment_verifier_rejects_static_directory_auth_token():
    with _hosted_fixture(FixtureOptions(static_auth_token=True)) as base_url:
        completed = _run_verifier(
            "--allow-http",
            "--skip-web",
            "--directory-url",
            f"{base_url}/directory/servers.json",
        )

    assert completed.returncode == 1
    assert "[FAIL] server directory" in completed.stdout
    assert "embeds static auth_token" in completed.stderr


def test_hosted_deployment_verifier_rejects_cacheable_session_tokens():
    with _hosted_fixture(FixtureOptions(token_no_store=False)) as base_url:
        completed = _run_verifier(
            "--allow-http",
            "--skip-web",
            "--directory-url",
            f"{base_url}/directory/servers.json",
        )

    assert completed.returncode == 1
    assert "[FAIL] server directory" in completed.stdout
    assert "session_token_url must return Cache-Control: no-store" in completed.stderr


def test_hosted_deployment_verifier_rejects_unquoted_directory_etag():
    with _hosted_fixture(FixtureOptions(etag="groundfire-directory-v1")) as base_url:
        completed = _run_verifier(
            "--allow-http",
            "--skip-web",
            "--directory-url",
            f"{base_url}/directory/servers.json",
        )

    assert completed.returncode == 1
    assert "[FAIL] server directory" in completed.stdout
    assert "directory ETag must be quoted" in completed.stderr


def test_hosted_deployment_verifier_reports_network_errors_without_traceback():
    completed = _run_verifier(
        "--allow-http",
        "--skip-directory",
        "--web-url",
        "http://127.0.0.1:1/index.html",
    )

    assert completed.returncode == 1
    assert "[FAIL] web export" in completed.stdout
    assert "web URL request failed" in completed.stderr
    assert "Traceback" not in completed.stderr


def _run_verifier(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--timeout", "5", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


@contextmanager
def _hosted_fixture(options: FixtureOptions = FixtureOptions()) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(options))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _handler_for(options: FixtureOptions) -> type[BaseHTTPRequestHandler]:
    class HostedFixtureHandler(BaseHTTPRequestHandler):
        server_version = "GroundfireHostedFixture/1"

        def do_HEAD(self) -> None:
            path = urlsplit(self.path).path
            if path in {"/index.wasm", "/index.pck"}:
                self._send_artifact(path, send_body=False)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "not found")

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path in {"/", "/index.html"}:
                self._send_index()
                return
            if path in {"/index.wasm", "/index.pck"}:
                self._send_artifact(path, send_body=True)
                return
            if path == "/directory/servers.json":
                self._send_directory()
                return
            if path == "/directory/session-token.json":
                self._send_session_token()
                return
            if path == "/directory/healthz":
                self._send_json({"ok": True, "schema": 1, "served_servers": 1})
                return
            if path == "/directory/diagnostics.json":
                self._send_json({"ok": True, "schema": 1, "served_servers": 1, "invalid_servers": []})
                return
            self.send_error(HTTPStatus.NOT_FOUND, "not found")

        def log_message(self, _format: str, *_args: object) -> None:
            return

        def _send_index(self) -> None:
            body = (
                "<!doctype html><html><head><title>Groundfire Godot</title></head>"
                "<body><script>const GODOT_CONFIG = "
                '{"executable":"index","fileSizes":{"index.wasm":10,"index.pck":10}};'
                "</script></body></html>"
            ).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=60, must-revalidate")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_artifact(self, path: str, *, send_body: bool) -> None:
            body = b"\0asmfixture" if path.endswith(".wasm") else b"pckfixture"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/wasm" if path.endswith(".wasm") else "application/octet-stream")
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def _send_directory(self) -> None:
            if self.headers.get("If-None-Match") == options.etag:
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self._send_directory_headers(content_length=0)
                self.end_headers()
                return

            host = self.headers.get("Host", "127.0.0.1")
            server = {
                "name": "Hosted Fixture",
                "game": "Groundfire",
                "players": "1/8",
                "map": "classic",
                "latency": "20ms",
                "source": "online",
                "endpoint": "wss://play.example.test/gateway",
                "passworded": False,
                "session_token_url": f"http://{host}/directory/session-token.json",
            }
            if options.static_auth_token:
                server["auth_token"] = "static-secret"
            body = json.dumps({"schema": 1, "servers": [server]}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self._send_directory_headers(content_length=len(body))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def _send_directory_headers(self, *, content_length: int) -> None:
            self.send_header("Cache-Control", "public, max-age=30, must-revalidate")
            self.send_header("ETag", options.etag)
            self.send_header("X-Groundfire-Directory-Refresh", "30")
            self.send_header("Content-Length", str(content_length))

        def _send_session_token(self) -> None:
            params = parse_qs(urlsplit(self.path).query)
            player_name = params.get("player_name", [""])[0]
            body = json.dumps({"ok": True, "schema": 1, "auth_token": f"token-for-{player_name}"}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header(
                "Cache-Control",
                "no-store" if options.token_no_store else "public, max-age=60, must-revalidate",
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, payload: dict[str, object]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=30, must-revalidate")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return HostedFixtureHandler
