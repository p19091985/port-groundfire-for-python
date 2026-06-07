from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass, replace
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from groundfire_net.browser import ServerBook, ServerListEntry
from groundfire_net.websocket_gateway import DEFAULT_SESSION_TOKEN_TTL_SECONDS, generate_join_token

DIRECTORY_SCHEMA_VERSION = 1
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 27880
DEFAULT_REFRESH_SECONDS = 30
DEFAULT_CACHE_SECONDS = 30
DEFAULT_DIRECTORY_PATH = Path("godot/data/server_directory.json")
REQUIRED_SERVER_FIELDS = ("name", "game", "players", "map", "latency", "source", "endpoint", "passworded")
STRING_SERVER_FIELDS = ("name", "game", "players", "map", "latency", "source", "endpoint")
OPTIONAL_STRING_SERVER_FIELDS = ("region", "description", "version", "auth_token", "session_token_url")
OPTIONAL_ARRAY_SERVER_FIELDS = ("tags",)
OPTIONAL_INTEGER_SERVER_FIELDS = ("last_seen_msec",)


@dataclass(frozen=True)
class DirectoryServiceConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    directory_path: Path = DEFAULT_DIRECTORY_PATH
    include_lan: bool = False
    gateway_endpoint: str = ""
    server_name: str = "Groundfire Gateway"
    cache_seconds: int = DEFAULT_CACHE_SECONDS
    refresh_seconds: int = DEFAULT_REFRESH_SECONDS
    cors_origin: str = "*"
    session_secret: str = ""
    session_token_ttl: int = DEFAULT_SESSION_TOKEN_TTL_SECONDS
    session_token_url: str = ""
    allow_static_auth_tokens: bool = False
    require_github_oauth: bool = False


def load_directory_payload(config: DirectoryServiceConfig) -> dict[str, Any]:
    payload = _load_payload_from_path(config.directory_path)
    servers = _servers_from_payload(
        payload,
        include_lan=config.include_lan,
        allow_static_auth_tokens=config.allow_static_auth_tokens,
    )
    if config.gateway_endpoint and _is_valid_online_endpoint(config.gateway_endpoint):
        servers.insert(0, _gateway_entry(config))
    return {
        "schema": DIRECTORY_SCHEMA_VERSION,
        "servers": _unique_servers(servers),
    }


def directory_diagnostics(config: DirectoryServiceConfig) -> dict[str, Any]:
    payload = _load_payload_from_path(config.directory_path)
    invalid_servers: list[dict[str, Any]] = []
    filtered_lan_servers = 0
    accepted_servers = 0
    raw_servers = payload.get("servers", [])
    if payload.get("schema") == DIRECTORY_SCHEMA_VERSION and isinstance(raw_servers, list):
        for index, server in enumerate(raw_servers):
            if not isinstance(server, dict):
                invalid_servers.append({"index": index, "errors": ["server must be object"]})
                continue
            errors = directory_server_errors(
                server,
                allow_static_auth_tokens=config.allow_static_auth_tokens,
            )
            if errors:
                invalid_servers.append({"index": index, "endpoint": str(server.get("endpoint", "")), "errors": errors})
                continue
            if not config.include_lan and server.get("source") == "lan":
                filtered_lan_servers += 1
                continue
            accepted_servers += 1
    elif payload.get("schema") == DIRECTORY_SCHEMA_VERSION:
        invalid_servers.append({"index": -1, "errors": ["servers must be array"]})
    invalid_gateway_endpoint = bool(config.gateway_endpoint and not _is_valid_online_endpoint(config.gateway_endpoint))
    served_payload = load_directory_payload(config)
    return {
        "ok": not invalid_servers and not invalid_gateway_endpoint,
        "schema": DIRECTORY_SCHEMA_VERSION,
        "source_path": str(config.directory_path),
        "include_lan": config.include_lan,
        "allow_static_auth_tokens": config.allow_static_auth_tokens,
        "accepted_servers": accepted_servers,
        "served_servers": len(served_payload["servers"]),
        "filtered_lan_servers": filtered_lan_servers,
        "invalid_servers": invalid_servers,
        "invalid_gateway_endpoint": invalid_gateway_endpoint,
    }


def response_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def response_etag(body: bytes) -> str:
    return f'"{hashlib.sha256(body).hexdigest()}"'


def server_entry_to_directory(entry: ServerListEntry) -> dict[str, Any]:
    source = "online" if entry.source in {"internet", "online"} else "lan"
    endpoint = _online_endpoint(entry) if source == "online" else entry.endpoint
    directory_entry: dict[str, Any] = {
        "name": entry.name,
        "game": entry.game,
        "players": f"{entry.player_count}/{entry.max_players}",
        "map": entry.map_name,
        "latency": "LAN" if entry.latency_ms is None else f"{entry.latency_ms}ms",
        "source": source,
        "endpoint": endpoint,
        "passworded": entry.requires_password,
        "region": entry.region,
        "description": entry.description,
        "version": str(entry.protocol_version),
    }
    return {key: value for key, value in directory_entry.items() if value not in {"", None}}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve the Groundfire Godot server directory schema over HTTP.")
    parser.add_argument("--host", default=os.environ.get("GROUNDFIRE_DIRECTORY_HOST", DEFAULT_HOST))
    parser.add_argument(
        "--port",
        type=_non_negative_int,
        default=_environment_int("GROUNDFIRE_DIRECTORY_PORT", DEFAULT_PORT),
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path(os.environ.get("GROUNDFIRE_DIRECTORY_PATH", str(DEFAULT_DIRECTORY_PATH))),
        help="Path to a schema 1 Godot directory JSON file or a Python ServerBook JSON file.",
    )
    parser.add_argument(
        "--include-lan",
        action="store_true",
        default=_environment_bool("GROUNDFIRE_DIRECTORY_INCLUDE_LAN", False),
        help="Include LAN entries for local desktop development. Public web directories should leave this off.",
    )
    parser.add_argument(
        "--gateway-endpoint",
        default=os.environ.get("GROUNDFIRE_DIRECTORY_GATEWAY_ENDPOINT", ""),
        help="Optional ws:// or wss:// endpoint to inject as the first online server.",
    )
    parser.add_argument(
        "--server-name",
        default=os.environ.get("GROUNDFIRE_DIRECTORY_SERVER_NAME", "Groundfire Gateway"),
    )
    parser.add_argument(
        "--cache-seconds",
        type=_non_negative_int,
        default=_environment_int("GROUNDFIRE_DIRECTORY_CACHE_SECONDS", DEFAULT_CACHE_SECONDS),
    )
    parser.add_argument(
        "--refresh-seconds",
        type=_non_negative_int,
        default=_environment_int("GROUNDFIRE_DIRECTORY_REFRESH_SECONDS", DEFAULT_REFRESH_SECONDS),
    )
    parser.add_argument("--cors-origin", default=os.environ.get("GROUNDFIRE_DIRECTORY_CORS_ORIGIN", "*"))
    parser.add_argument(
        "--session-secret",
        default=os.environ.get("GROUNDFIRE_DIRECTORY_SESSION_SECRET", ""),
        help=(
            "Optional HMAC secret for /session-token.json. Must match the gateway "
            "--session-secret / GROUNDFIRE_WEB_GATEWAY_SESSION_SECRET value."
        ),
    )
    parser.add_argument(
        "--session-token-ttl",
        type=_positive_int,
        default=_environment_positive_int(
            "GROUNDFIRE_DIRECTORY_SESSION_TOKEN_TTL",
            DEFAULT_SESSION_TOKEN_TTL_SECONDS,
        ),
        help="Lifetime, in seconds, for tokens returned by /session-token.json.",
    )
    parser.add_argument(
        "--session-token-url",
        default=os.environ.get("GROUNDFIRE_DIRECTORY_SESSION_TOKEN_URL", ""),
        help=(
            "Optional public URL for the session-token issuer advertised on injected gateway entries. "
            "Defaults to this directory service's /session-token.json when --session-secret is enabled."
        ),
    )
    parser.add_argument(
        "--allow-static-auth-tokens",
        action="store_true",
        default=_environment_bool("GROUNDFIRE_DIRECTORY_ALLOW_STATIC_AUTH_TOKENS", False),
        help=(
            "Permit directory entries that embed auth_token. Keep this off for public directories; "
            "use session_token_url and /session-token.json instead."
        ),
    )
    parser.add_argument(
        "--require-github-oauth",
        action="store_true",
        default=_environment_bool("GROUNDFIRE_DIRECTORY_REQUIRE_GITHUB_OAUTH", False),
        help="Enforce that /session-token.json requests provide a valid GitHub OAuth token in the Authorization header.",
    )
    return parser


def serve_forever(config: DirectoryServiceConfig) -> None:
    server = build_http_server(config)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def build_http_server(config: DirectoryServiceConfig) -> ThreadingHTTPServer:
    handler = _handler_for_config(config)
    return ThreadingHTTPServer((config.host, config.port), handler)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = DirectoryServiceConfig(
        host=args.host,
        port=args.port,
        directory_path=args.directory,
        include_lan=args.include_lan,
        gateway_endpoint=args.gateway_endpoint,
        server_name=args.server_name,
        cache_seconds=args.cache_seconds,
        refresh_seconds=args.refresh_seconds,
        cors_origin=args.cors_origin,
        session_secret=args.session_secret,
        session_token_ttl=args.session_token_ttl,
        session_token_url=args.session_token_url,
        allow_static_auth_tokens=args.allow_static_auth_tokens,
        require_github_oauth=args.require_github_oauth,
    )
    serve_forever(config)
    return 0


def _handler_for_config(config: DirectoryServiceConfig) -> type[BaseHTTPRequestHandler]:
    class GroundfireDirectoryHandler(BaseHTTPRequestHandler):
        server_version = "GroundfireDirectory/1"

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self._write_common_headers("0", "")
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, If-None-Match")
            self.end_headers()

        def do_HEAD(self) -> None:
            parsed = urlsplit(self.path)
            if parsed.path in {"/", "/servers.json"}:
                self._send_directory(send_body=False)
                return
            if parsed.path == "/session-token.json":
                self._send_session_token(parsed.query, send_body=False)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "not found")

        def do_GET(self) -> None:
            parsed = urlsplit(self.path)
            if parsed.path in {"/healthz", "/health"}:
                diagnostics = directory_diagnostics(config)
                self._send_json(
                    {
                        "ok": True,
                        "schema": DIRECTORY_SCHEMA_VERSION,
                        "served_servers": diagnostics["served_servers"],
                        "invalid_servers": len(diagnostics["invalid_servers"]),
                        "filtered_lan_servers": diagnostics["filtered_lan_servers"],
                    }
                )
                return
            if parsed.path == "/schema.json":
                self._send_json(_schema_payload())
                return
            if parsed.path == "/diagnostics.json":
                self._send_json(directory_diagnostics(config))
                return
            if parsed.path == "/session-token.json":
                self._send_session_token(parsed.query, send_body=True)
                return
            if parsed.path in {"/", "/servers.json"}:
                self._send_directory(send_body=True)
                return
            self.send_error(HTTPStatus.NOT_FOUND, "not found")

        def log_message(self, _format: str, *_args: Any) -> None:
            return

        def _send_directory(self, *, send_body: bool) -> None:
            payload = load_directory_payload(config)
            body = response_bytes(payload)
            etag = response_etag(body)
            if _etag_matches(self.headers.get("If-None-Match", ""), etag):
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self._write_common_headers("0", etag)
                self.end_headers()
                return
            self.send_response(HTTPStatus.OK)
            self._write_common_headers(str(len(body)), etag)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def _send_session_token(self, query: str, *, send_body: bool) -> None:
            if not config.session_secret:
                self._send_session_error(HTTPStatus.NOT_FOUND, "session_tokens_disabled", send_body=send_body)
                return
            params = parse_qs(query, keep_blank_values=True)
            player_name = str(params.get("player_name", [""])[0]).strip()
            if not player_name:
                self._send_session_error(HTTPStatus.BAD_REQUEST, "missing_player_name", send_body=send_body)
                return
            
            if config.require_github_oauth:
                auth_header = self.headers.get("Authorization", "")
                if not auth_header.lower().startswith("bearer "):
                    self._send_session_error(HTTPStatus.UNAUTHORIZED, "missing_oauth_token", send_body=send_body)
                    return
                github_token = auth_header[7:].strip()
                if not _verify_github_token(github_token, player_name):
                    self._send_session_error(HTTPStatus.FORBIDDEN, "invalid_github_token_or_username", send_body=send_body)
                    return

            token = generate_join_token(
                config.session_secret,
                player_name,
                ttl_seconds=max(1, int(config.session_token_ttl)),
            )
            body = response_bytes(
                {
                    "ok": True,
                    "schema": DIRECTORY_SCHEMA_VERSION,
                    "token_type": "groundfire_join",
                    "auth_token": token,
                    "player_name": player_name,
                    "expires_in": max(1, int(config.session_token_ttl)),
                }
            )
            self.send_response(HTTPStatus.OK)
            self._write_token_headers(str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def _send_session_error(self, status: HTTPStatus, message: str, *, send_body: bool) -> None:
            body = response_bytes({"ok": False, "schema": DIRECTORY_SCHEMA_VERSION, "error": message})
            self.send_response(status)
            self._write_token_headers(str(len(body)))
            self.end_headers()
            if send_body:
                self.wfile.write(body)

        def _send_json(self, payload: dict[str, Any]) -> None:
            body = response_bytes(payload)
            self.send_response(HTTPStatus.OK)
            self._write_common_headers(str(len(body)), response_etag(body))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def _write_common_headers(self, content_length: str, etag: str) -> None:
            self.send_header("Access-Control-Allow-Origin", config.cors_origin)
            self.send_header("Cache-Control", f"public, max-age={config.cache_seconds}, must-revalidate")
            self.send_header("X-Groundfire-Directory-Refresh", str(config.refresh_seconds))
            if etag:
                self.send_header("ETag", etag)
            self.send_header("Content-Length", content_length)

        def _write_token_headers(self, content_length: str) -> None:
            self.send_header("Access-Control-Allow-Origin", config.cors_origin)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", content_length)

    return GroundfireDirectoryHandler


def _load_payload_from_path(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema": DIRECTORY_SCHEMA_VERSION, "servers": []}


def _servers_from_payload(
    payload: dict[str, Any],
    *,
    include_lan: bool,
    allow_static_auth_tokens: bool,
) -> list[dict[str, Any]]:
    if payload.get("schema") == DIRECTORY_SCHEMA_VERSION and isinstance(payload.get("servers"), list):
        return [
            dict(server)
            for server in payload["servers"]
            if (
                isinstance(server, dict)
                and not directory_server_errors(server, allow_static_auth_tokens=allow_static_auth_tokens)
                and (include_lan or server.get("source") != "lan")
            )
        ]
    book = ServerBook(None)
    book._internet = book._decode_entries(payload.get("internet", ()))
    entries = list(book.get_internet())
    if include_lan:
        entries.extend(book._decode_entries(payload.get("favorites", ())))
        entries.extend(book._decode_entries(payload.get("history", ())))
    return [server_entry_to_directory(entry) for entry in entries]


def _gateway_entry(config: DirectoryServiceConfig) -> dict[str, Any]:
    entry = {
        "name": config.server_name,
        "game": "Groundfire",
        "players": "0/8",
        "map": "classic",
        "latency": "0ms",
        "source": "online",
        "endpoint": config.gateway_endpoint,
        "passworded": False,
        "description": "Local browser-safe gateway directory entry",
    }
    session_token_url = _session_token_url(config)
    if session_token_url:
        entry["session_token_url"] = session_token_url
    return entry


def _session_token_url(config: DirectoryServiceConfig) -> str:
    if config.session_token_url:
        return config.session_token_url
    if not config.session_secret or config.port <= 0:
        return ""
    host = "127.0.0.1" if config.host in {"", "0.0.0.0", "::"} else config.host
    return f"http://{host}:{config.port}/session-token.json"


def _schema_payload() -> dict[str, Any]:
    return {
        "schema": DIRECTORY_SCHEMA_VERSION,
        "servers": {
            "required": list(REQUIRED_SERVER_FIELDS),
            "sources": ["online", "lan"],
            "online_endpoint": "ws:// or wss://",
            "passworded": "boolean",
            "auth_token": (
                "private/dev only; rejected by public groundfire-directory "
                "unless --allow-static-auth-tokens is enabled"
            ),
            "session_token_url": "http:// or https:// no-store signed-token issuer",
        },
    }


def _unique_servers(servers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for server in servers:
        endpoint = str(server.get("endpoint", ""))
        if not endpoint or endpoint in seen:
            continue
        seen.add(endpoint)
        unique.append(server)
    return unique


def _etag_matches(header_value: str, etag: str) -> bool:
    normalized_etag = etag.strip()
    legacy_unquoted_etag = normalized_etag.strip('"')
    for token in header_value.split(","):
        candidate = token.strip()
        if candidate == "*" or candidate == normalized_etag:
            return True
        if candidate == legacy_unquoted_etag:
            return True
    return False


def _online_endpoint(entry: ServerListEntry) -> str:
    scheme = "wss" if entry.secure else "ws"
    return f"{scheme}://{entry.host}:{entry.port}"


def directory_server_errors(server: dict[str, Any], *, allow_static_auth_tokens: bool = True) -> list[str]:
    errors: list[str] = []
    for field_name in REQUIRED_SERVER_FIELDS:
        if field_name not in server:
            errors.append(f"{field_name} is required")
    for field_name in STRING_SERVER_FIELDS:
        if field_name in server and not _is_non_empty_string(server[field_name]):
            errors.append(f"{field_name} must be a non-empty string")
    if "passworded" in server and not isinstance(server["passworded"], bool):
        errors.append("passworded must be boolean")
    source = str(server.get("source", ""))
    if source not in {"online", "lan"}:
        errors.append("source must be online or lan")
    endpoint = str(server.get("endpoint", ""))
    if source == "online" and not _is_valid_online_endpoint(endpoint):
        errors.append("endpoint must be ws:// or wss:// for online servers")
    for field_name in OPTIONAL_STRING_SERVER_FIELDS:
        if field_name in server and not isinstance(server[field_name], str):
            errors.append(f"{field_name} must be string")
    if not allow_static_auth_tokens and str(server.get("auth_token", "")).strip():
        errors.append("auth_token is not allowed in public directory entries; use session_token_url")
    raw_session_token_url = server.get("session_token_url", "")
    session_token_url = raw_session_token_url.strip() if isinstance(raw_session_token_url, str) else ""
    if session_token_url and not _is_valid_http_endpoint(session_token_url):
        errors.append("session_token_url must be http:// or https://")
    for field_name in OPTIONAL_ARRAY_SERVER_FIELDS:
        if field_name in server and not isinstance(server[field_name], list):
            errors.append(f"{field_name} must be array")
    for field_name in OPTIONAL_INTEGER_SERVER_FIELDS:
        if field_name in server and (not isinstance(server[field_name], int) or isinstance(server[field_name], bool)):
            errors.append(f"{field_name} must be integer")
    return errors


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_valid_online_endpoint(endpoint: str) -> bool:
    return endpoint.startswith(("ws://", "wss://"))


def _is_valid_http_endpoint(endpoint: str) -> bool:
    return endpoint.startswith(("http://", "https://"))


def _verify_github_token(token: str, expected_username: str) -> bool:
    import urllib.request
    import urllib.error
    req = urllib.request.Request("https://api.github.com/user")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "Groundfire-Directory/1.0")
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode("utf-8"))
                return str(data.get("login", "")).lower() == expected_username.lower()
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        pass
    return False


def _environment_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _environment_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be greater than or equal to 0")
    return parsed


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _environment_positive_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def config_with_port(config: DirectoryServiceConfig, port: int) -> DirectoryServiceConfig:
    return replace(config, port=port)


if __name__ == "__main__":
    raise SystemExit(main())
