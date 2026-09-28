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

    @property
    def database_path(self) -> Path:
        path = Path(self.database)
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
    )
    if not 1 <= settings.port <= 65535:
        raise ValueError("service.port must be between 1 and 65535")
    if settings.reservation_ttl_seconds < 5 or settings.queue_ttl_seconds < 10:
        raise ValueError("match timeouts are too small")
    return settings
