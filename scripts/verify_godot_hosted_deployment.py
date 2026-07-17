#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

DEFAULT_WEB_URL = "https://play.groundfire.net/"
DEFAULT_DIRECTORY_URL = "https://play.groundfire.net/directory/servers.json"
DEFAULT_PLAYER_NAME = "GodotPlayer"
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_HTML_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 512 * 1024
USER_AGENT = "GroundfireHostedDeploymentVerifier/1"
REQUIRED_DIRECTORY_FIELDS = ("name", "game", "players", "map", "latency", "source", "endpoint", "passworded")
ASSET_REF_RE = re.compile(r"(?P<ref>(?:https?://)?[A-Za-z0-9_./%+-]+?\.(?:wasm|pck))(?:[?#][^\"'<>\s]*)?")


@dataclass(frozen=True)
class HttpResult:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes
    error: str = ""


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if value and name.lower() in {"href", "src"}:
                self.refs.append(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify that the hosted Groundfire Godot web build and public directory are production-shaped."
    )
    parser.add_argument("--web-url", default=DEFAULT_WEB_URL)
    parser.add_argument("--directory-url", default=DEFAULT_DIRECTORY_URL)
    parser.add_argument("--player-name", default=DEFAULT_PLAYER_NAME)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Allow http:// and ws:// URLs for local staging tests.",
    )
    parser.add_argument("--skip-web", action="store_true", help="Skip web export checks.")
    parser.add_argument("--skip-directory", action="store_true", help="Skip public directory checks.")
    parser.add_argument(
        "--require-session-token",
        action="store_true",
        help="Require every online directory entry to advertise session_token_url.",
    )
    parser.add_argument("--health-url", default="", help="Optional hosted health endpoint to verify as JSON.")
    parser.add_argument("--diagnostics-url", default="", help="Optional hosted diagnostics endpoint to verify as JSON.")
    return parser


def verify_web_export(web_url: str, *, timeout: float, allow_http: bool) -> list[str]:
    errors: list[str] = []
    _require_public_url(web_url, allow_http=allow_http, label="web URL", errors=errors)
    if errors:
        return errors

    result = _request(web_url, timeout=timeout, read_limit=MAX_HTML_BYTES)
    if result.status != 200:
        return [_status_error("web URL", web_url, result)]

    if not _header(result, "cache-control"):
        errors.append("web index is missing Cache-Control")

    html = result.body.decode("utf-8", errors="replace")
    if "godot" not in html.lower():
        errors.append("web index does not look like a Godot web export")

    asset_urls = _asset_urls_from_html(result.url, html)
    wasm_urls = [url for url in asset_urls if urlsplit(url).path.endswith(".wasm")]
    pck_urls = [url for url in asset_urls if urlsplit(url).path.endswith(".pck")]
    if not wasm_urls:
        errors.append("web index does not reference a .wasm artifact")
    if not pck_urls:
        errors.append("web index does not reference an .pck artifact")

    for asset_url in wasm_urls + pck_urls:
        errors.extend(_verify_web_artifact(asset_url, timeout=timeout, allow_http=allow_http))

    return errors


def verify_directory(
    directory_url: str,
    *,
    timeout: float,
    allow_http: bool,
    player_name: str,
    require_session_token: bool,
) -> list[str]:
    errors: list[str] = []
    _require_public_url(directory_url, allow_http=allow_http, label="directory URL", errors=errors)
    if errors:
        return errors

    result = _request(directory_url, timeout=timeout, read_limit=MAX_JSON_BYTES)
    if result.status != 200:
        return [_status_error("directory URL", directory_url, result)]

    if not _header(result, "cache-control"):
        errors.append("directory response is missing Cache-Control")

    refresh_header = _header(result, "x-groundfire-directory-refresh")
    if not refresh_header:
        errors.append("directory response is missing X-Groundfire-Directory-Refresh")
    elif not refresh_header.isdigit():
        errors.append("directory X-Groundfire-Directory-Refresh must be an integer")

    etag = _header(result, "etag")
    if not etag:
        errors.append("directory response is missing ETag")
    elif not (etag.startswith('"') and etag.endswith('"')):
        errors.append("directory ETag must be quoted")
    else:
        conditional = _request(
            directory_url,
            timeout=timeout,
            read_limit=0,
            headers={"If-None-Match": etag},
        )
        if conditional.status != 304:
            if conditional.error:
                errors.append(_request_error("directory conditional If-None-Match", directory_url, conditional))
            else:
                errors.append(f"directory conditional If-None-Match expected 304, got HTTP {conditional.status}")

    payload = _json_payload(result, label="directory", errors=errors)
    if not isinstance(payload, dict):
        return errors

    if payload.get("schema") != 1:
        errors.append("directory payload must declare schema 1")

    servers = payload.get("servers")
    if not isinstance(servers, list):
        errors.append("directory payload must include a servers array")
        return errors

    for index, server in enumerate(servers):
        if not isinstance(server, dict):
            errors.append(f"directory server {index} must be an object")
            continue
        errors.extend(
            _verify_directory_server(
                server,
                index=index,
                timeout=timeout,
                allow_http=allow_http,
                player_name=player_name,
                require_session_token=require_session_token,
            )
        )

    return errors


def verify_json_endpoint(url: str, *, timeout: float, allow_http: bool, label: str) -> list[str]:
    errors: list[str] = []
    if not url:
        return errors
    _require_public_url(url, allow_http=allow_http, label=label, errors=errors)
    if errors:
        return errors

    result = _request(url, timeout=timeout, read_limit=MAX_JSON_BYTES)
    if result.status != 200:
        return [_status_error(label, url, result)]

    payload = _json_payload(result, label=label, errors=errors)
    if isinstance(payload, dict) and payload.get("ok") is False:
        errors.append(f"{label} reports ok=false")
    return errors


def _verify_web_artifact(asset_url: str, *, timeout: float, allow_http: bool) -> list[str]:
    errors: list[str] = []
    _require_public_url(asset_url, allow_http=allow_http, label="web artifact", errors=errors)
    if errors:
        return errors

    result = _request(asset_url, timeout=timeout, read_limit=0, method="HEAD")
    if result.status in {405, 501}:
        result = _request(asset_url, timeout=timeout, read_limit=1, method="GET")
    if result.status != 200:
        return [_status_error("web artifact", asset_url, result)]

    if not _header(result, "cache-control"):
        errors.append(f"web artifact is missing Cache-Control: {asset_url}")

    if urlsplit(asset_url).path.endswith(".wasm"):
        content_type = _header(result, "content-type")
        if "application/wasm" not in content_type.lower():
            errors.append(f".wasm artifact must be served as application/wasm: {asset_url}")

    return errors


def _verify_directory_server(
    server: dict[str, Any],
    *,
    index: int,
    timeout: float,
    allow_http: bool,
    player_name: str,
    require_session_token: bool,
) -> list[str]:
    errors: list[str] = []
    prefix = f"directory server {index}"

    for field in REQUIRED_DIRECTORY_FIELDS:
        if field not in server:
            errors.append(f"{prefix} is missing {field}")

    if server.get("auth_token"):
        errors.append(f"{prefix} embeds static auth_token; public directories must use session_token_url")

    source = server.get("source")
    endpoint = server.get("endpoint")
    if source == "online":
        if not isinstance(endpoint, str) or not endpoint:
            errors.append(f"{prefix} online endpoint must be a non-empty string")
        else:
            endpoint_scheme = urlsplit(endpoint).scheme
            if endpoint_scheme not in {"ws", "wss"}:
                errors.append(f"{prefix} online endpoint must use ws:// or wss://")
            elif endpoint_scheme != "wss" and not allow_http:
                errors.append(f"{prefix} public online endpoint must use wss://")

    session_token_url = server.get("session_token_url")
    if session_token_url:
        if not isinstance(session_token_url, str):
            errors.append(f"{prefix} session_token_url must be a string")
        else:
            token_url_errors: list[str] = []
            _require_public_url(
                session_token_url,
                allow_http=allow_http,
                label=f"{prefix} session_token_url",
                errors=token_url_errors,
            )
            errors.extend(token_url_errors)
            if not token_url_errors:
                errors.extend(_verify_session_token(session_token_url, player_name=player_name, timeout=timeout))
    elif require_session_token and source == "online":
        errors.append(f"{prefix} is missing session_token_url")

    return errors


def _verify_session_token(session_token_url: str, *, player_name: str, timeout: float) -> list[str]:
    errors: list[str] = []
    result = _request(_with_player_name(session_token_url, player_name), timeout=timeout, read_limit=MAX_JSON_BYTES)
    if result.status != 200:
        return [_status_error("session_token_url", session_token_url, result)]

    if "no-store" not in _header(result, "cache-control").lower():
        errors.append(f"session_token_url must return Cache-Control: no-store: {session_token_url}")

    payload = _json_payload(result, label="session_token_url", errors=errors)
    if isinstance(payload, dict):
        token = payload.get("auth_token")
        if not isinstance(token, str) or not token:
            errors.append(f"session_token_url response must include non-empty auth_token: {session_token_url}")
    return errors


def _request(
    url: str,
    *,
    timeout: float,
    read_limit: int,
    method: str = "GET",
    headers: dict[str, str] | None = None,
) -> HttpResult:
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, headers=request_headers, method=method)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            body = _read_limited(response, read_limit)
            return HttpResult(
                url=response.geturl(),
                status=int(response.getcode()),
                headers=_normalize_headers(response.headers.items()),
                body=body,
            )
    except urllib.error.HTTPError as error:
        body = _read_limited(error, read_limit)
        return HttpResult(
            url=error.geturl(),
            status=int(error.code),
            headers=_normalize_headers(error.headers.items() if error.headers else ()),
            body=body,
        )
    except urllib.error.URLError as error:
        reason = getattr(error, "reason", error)
        return HttpResult(url=url, status=0, headers={}, body=b"", error=str(reason))
    except (OSError, TimeoutError, ssl.SSLError) as error:
        return HttpResult(url=url, status=0, headers={}, body=b"", error=str(error))


def _status_error(label: str, url: str, result: HttpResult) -> str:
    if result.error:
        return _request_error(label, url, result)
    return f"{label} returned HTTP {result.status}: {url}"


def _request_error(label: str, url: str, result: HttpResult) -> str:
    return f"{label} request failed for {url}: {result.error}"


def _read_limited(response: Any, read_limit: int) -> bytes:
    if read_limit <= 0:
        return b""
    return response.read(read_limit + 1)[:read_limit]


def _normalize_headers(items: Any) -> dict[str, str]:
    return {str(key).lower(): str(value) for key, value in items}


def _header(result: HttpResult, name: str) -> str:
    return result.headers.get(name.lower(), "")


def _json_payload(result: HttpResult, *, label: str, errors: list[str]) -> Any:
    try:
        return json.loads(result.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label} response is not valid JSON: {exc}")
        return None


def _asset_urls_from_html(base_url: str, html: str) -> list[str]:
    parser = _AssetReferenceParser()
    parser.feed(html)
    refs = list(parser.refs)
    refs.extend(match.group("ref") for match in ASSET_REF_RE.finditer(html))

    urls: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        path = urlsplit(ref).path
        if not (path.endswith(".wasm") or path.endswith(".pck")):
            continue
        url = urljoin(base_url, ref)
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _require_public_url(url: str, *, allow_http: bool, label: str, errors: list[str]) -> None:
    scheme = urlsplit(url).scheme
    if scheme == "https":
        return
    if allow_http and scheme == "http":
        return
    errors.append(f"{label} must use https:// for public verification: {url}")


def _with_player_name(url: str, player_name: str) -> str:
    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    query.append(("player_name", player_name))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _print_section(name: str, errors: list[str]) -> None:
    if errors:
        print(f"[FAIL] {name}")
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return
    print(f"[PASS] {name}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sections: list[tuple[str, list[str]]] = []

    if not args.skip_web:
        sections.append(
            (
                "web export",
                verify_web_export(args.web_url, timeout=args.timeout, allow_http=args.allow_http),
            )
        )
    if not args.skip_directory:
        sections.append(
            (
                "server directory",
                verify_directory(
                    args.directory_url,
                    timeout=args.timeout,
                    allow_http=args.allow_http,
                    player_name=args.player_name,
                    require_session_token=args.require_session_token,
                ),
            )
        )
    sections.append(
        (
            "optional hosted diagnostics",
            [
                *verify_json_endpoint(
                    args.health_url,
                    timeout=args.timeout,
                    allow_http=args.allow_http,
                    label="health URL",
                ),
                *verify_json_endpoint(
                    args.diagnostics_url,
                    timeout=args.timeout,
                    allow_http=args.allow_http,
                    label="diagnostics URL",
                ),
            ],
        )
    )

    for name, errors in sections:
        _print_section(name, errors)

    return 1 if any(errors for _name, errors in sections) else 0


if __name__ == "__main__":
    raise SystemExit(main())
