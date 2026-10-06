from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import tomllib


@dataclass(frozen=True)
class Settings:
    root: Path
    bind: str = "127.0.0.1"
    port: int = 27880
    public_base_url: str = "http://127.0.0.1:27880"
    allowed_origins: tuple[str, ...] = ("http://127.0.0.1:8060", "http://localhost:8060")
    database: str = "data/service.sqlite3"
    access_ttl_seconds: int = 900
    refresh_ttl_seconds: int = 2_592_000
    presence_ttl_seconds: int = 60
    invite_ttl_seconds: int = 600
    reservation_ttl_seconds: int = 30
    queue_ttl_seconds: int = 300
    max_workers: int = 8
    worker_bind: str = "127.0.0.1"
    worker_public_host: str = "127.0.0.1"
    worker_startup_seconds: float = 8.0
    admission_redeem_enabled: bool = True
    legacy_directory_enabled: bool = True
    legacy_directory_path: str = "conf/server_directory.json"
    legacy_include_lan: bool = False
    legacy_gateway_endpoint: str = ""
    legacy_server_name: str = "Groundfire Gateway"
    legacy_cache_seconds: int = 5
    legacy_refresh_seconds: int = 30
    legacy_session_secret: str = ""
    legacy_session_token_ttl_seconds: int = 3600
    legacy_session_token_url: str = ""
    legacy_allow_static_auth_tokens: bool = False
    legacy_require_github_oauth: bool = False
    legacy_master_enabled: bool = True
    legacy_master_bind: str = "127.0.0.1"
    legacy_master_port: int = 27017
    legacy_master_ttl_seconds: float = 90.0

    @property
    def database_path(self) -> Path:
        path = Path(self.database)
        return path if path.is_absolute() else self.root / path

    @property
    def legacy_directory_file(self) -> Path:
        path = Path(self.legacy_directory_path)
        return path if path.is_absolute() else self.root / path


def load_settings(root: Path | None = None, config_path: Path | None = None) -> Settings:
    package_root = (root or Path(__file__).resolve().parents[2]).resolve()
    selected = config_path or Path(os.environ.get("GF_SERVICE_CONFIG", package_root / "config.toml"))
    raw: dict = {}
    if selected.exists():
        with selected.open("rb") as stream:
            raw = tomllib.load(stream)
    service = raw.get("service", {})
    storage = raw.get("storage", {})
    identity = raw.get("identity", {})
    social = raw.get("social", {})
    matches = raw.get("matches", {})
    compatibility = raw.get("compatibility", {})
    settings = Settings(
        root=package_root,
        bind=str(service.get("bind", "127.0.0.1")),
        port=int(service.get("port", 27880)),
        public_base_url=str(service.get("public_base_url", "http://127.0.0.1:27880")).rstrip("/"),
        allowed_origins=tuple(
            str(value) for value in service.get("allowed_origins", ["http://127.0.0.1:8060", "http://localhost:8060"])
        ),
        database=str(storage.get("database", "data/service.sqlite3")),
        access_ttl_seconds=int(identity.get("access_ttl_seconds", 900)),
        refresh_ttl_seconds=int(identity.get("refresh_ttl_seconds", 2_592_000)),
        presence_ttl_seconds=int(social.get("presence_ttl_seconds", 60)),
        invite_ttl_seconds=int(social.get("invite_ttl_seconds", 600)),
        reservation_ttl_seconds=int(matches.get("reservation_ttl_seconds", 30)),
        queue_ttl_seconds=int(matches.get("queue_ttl_seconds", 300)),
        max_workers=int(matches.get("max_workers", 8)),
        worker_bind=str(matches.get("worker_bind", "127.0.0.1")),
        worker_public_host=str(matches.get("worker_public_host", service.get("bind", "127.0.0.1"))),
        worker_startup_seconds=float(matches.get("worker_startup_seconds", 8.0)),
        admission_redeem_enabled=bool(matches.get("admission_redeem_enabled", True)),
        legacy_directory_enabled=bool(compatibility.get("directory_enabled", True)),
        legacy_directory_path=str(compatibility.get("directory_path", "conf/server_directory.json")),
        legacy_include_lan=bool(compatibility.get("include_lan", False)),
        legacy_gateway_endpoint=str(compatibility.get("gateway_endpoint", "")),
        legacy_server_name=str(compatibility.get("server_name", "Groundfire Gateway")),
        legacy_cache_seconds=int(compatibility.get("cache_seconds", 5)),
        legacy_refresh_seconds=int(compatibility.get("refresh_seconds", 30)),
        legacy_session_secret=str(compatibility.get("session_secret", "")),
        legacy_session_token_ttl_seconds=int(compatibility.get("session_token_ttl_seconds", 3600)),
        legacy_session_token_url=str(compatibility.get("session_token_url", "")),
        legacy_allow_static_auth_tokens=bool(compatibility.get("allow_static_auth_tokens", False)),
        legacy_require_github_oauth=bool(compatibility.get("require_github_oauth", False)),
        legacy_master_enabled=bool(compatibility.get("master_enabled", True)),
        legacy_master_bind=str(compatibility.get("master_bind", "127.0.0.1")),
        legacy_master_port=int(compatibility.get("master_port", 27017)),
        legacy_master_ttl_seconds=float(compatibility.get("master_ttl_seconds", 90.0)),
    )
    if not 1 <= settings.port <= 65535:
        raise ValueError("service.port must be between 1 and 65535")
    if settings.reservation_ttl_seconds < 5 or settings.queue_ttl_seconds < 10:
        raise ValueError("match timeouts are too small")
    if not 0 <= settings.legacy_master_port <= 65535:
        raise ValueError("compatibility.master_port must be between 0 and 65535")
    if settings.legacy_master_ttl_seconds <= 0:
        raise ValueError("compatibility.master_ttl_seconds must be positive")
    if settings.legacy_cache_seconds < 0 or settings.legacy_refresh_seconds < 0:
        raise ValueError("compatibility cache and refresh values cannot be negative")
    if settings.legacy_session_token_ttl_seconds <= 0:
        raise ValueError("compatibility.session_token_ttl_seconds must be positive")
    return settings
