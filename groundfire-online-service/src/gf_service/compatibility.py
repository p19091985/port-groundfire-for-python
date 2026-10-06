from __future__ import annotations

import threading

from groundfire_net.directory_service import DirectoryServiceConfig
from groundfire_net.master import MasterServerApp, MasterServerDirectory

from .config import Settings


def directory_config(settings: Settings) -> DirectoryServiceConfig:
    return DirectoryServiceConfig(
        host=settings.bind,
        port=settings.port,
        directory_path=settings.legacy_directory_file,
        include_lan=settings.legacy_include_lan,
        gateway_endpoint=settings.legacy_gateway_endpoint,
        server_name=settings.legacy_server_name,
        cache_seconds=settings.legacy_cache_seconds,
        refresh_seconds=settings.legacy_refresh_seconds,
        cors_origin=settings.allowed_origins[0] if settings.allowed_origins else "*",
        session_secret=settings.legacy_session_secret,
        session_token_ttl=settings.legacy_session_token_ttl_seconds,
        session_token_url=settings.legacy_session_token_url,
        allow_static_auth_tokens=settings.legacy_allow_static_auth_tokens,
        require_github_oauth=settings.legacy_require_github_oauth,
    )


class LegacyMasterSupervisor:
    """Runs the protocol-1 UDP master as part of the unified service."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        directory = MasterServerDirectory(ttl_seconds=settings.legacy_master_ttl_seconds)
        self._app = MasterServerApp(
            host=settings.legacy_master_bind,
            port=settings.legacy_master_port,
            directory=directory,
        )

    @property
    def enabled(self) -> bool:
        return self.settings.legacy_master_enabled

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    @property
    def bound_port(self) -> int | None:
        return self._app.get_bound_port() if self.running else None

    def start(self) -> None:
        if not self.enabled or self.running:
            return
        self._stop.clear()
        self._app.open()
        self._thread = threading.Thread(target=self._run, name="groundfire-legacy-master", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._app.close()

    def _run(self) -> None:
        try:
            while not self._stop.is_set():
                self._app.poll(timeout=0.1)
        finally:
            self._app.close()
