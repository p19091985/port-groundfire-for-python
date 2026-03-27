from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.inifile import ReadIniFile


@dataclass(frozen=True)
class NetworkConfig:
    enabled: bool = False
    mode: str = "local"
    host: str = "127.0.0.1"
    port: int = 52625
    player_slot: int = 0
    client_name: str = "Player"
    online_ai_enabled: bool = False
    fallback_to_local_controls: bool = True

    @classmethod
    def from_settings(cls, settings: "ReadIniFile") -> "NetworkConfig":
        mode = settings.get_string("Network", "Mode", "local").strip().lower()
        if not mode:
            mode = "local"

        port = settings.get_int("Network", "Port", 52625)
        if port < 1:
            port = 52625

        player_slot = settings.get_int("Network", "PlayerSlot", 0)
        if player_slot < 0:
            player_slot = 0

        return cls(
            enabled=settings.get_int("Network", "Enabled", 0) != 0,
            mode=mode,
            host=settings.get_string("Network", "Host", "127.0.0.1"),
            port=port,
            player_slot=player_slot,
            client_name=settings.get_string("Network", "ClientName", "Player").strip() or "Player",
            online_ai_enabled=settings.get_int("Network", "OnlineAIEnabled", 0) != 0,
            fallback_to_local_controls=(
                settings.get_int("Network", "FallbackToLocalControls", 1) != 0
            ),
        )
